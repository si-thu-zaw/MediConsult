import secrets
import os
from PIL import Image
from datetime import timedelta, datetime
from flask import render_template, url_for, flash, redirect, request, abort, session
from mediconsult import app, db, bcrypt, mail, socketio
from mediconsult.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, RequestResetForm, ResetPasswordForm, ChangePasswordForm, AdminChangePasswordForm, MOTDForm, NewPatientForm, NewCaseForm, NoteForm, CommentForm, ResultForm, PrescriptionForm, HistoryForm
from mediconsult.models import User, Post, UserRole, motd, Patient, medcase, Comment, PatientNotes, History, Referral, Accesshistory, Result, Prescription
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=10)



#GENERAL PAGES

#HOME LOGIN PAGE
@app.route("/", methods=['GET', 'POST'])
@app.route("/home", methods=['GET', 'POST'])
def home():
    if current_user.is_authenticated:
        return redirect(url_for('account'))    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            user.last_login=datetime.utcnow()
            db.session.commit()
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect (next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')

    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(per_page=3, page=page)
    return render_template('index.html', form=form, posts=posts, title='Home')

#ABOUT PAGE
@app.route("/about")
def about():
    return render_template('about.html', title='About')

#CONTACT PAGE
@app.route("/contact")
def contact():
    return render_template('contact.html', title='Contact Us')

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_filename = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/images/profiles', picture_filename)
    
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    
    i.save(picture_path)
    
    return picture_filename

def save_file(form_file):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_file.filename)
    file_filename = random_hex + f_ext
    file_path = os.path.join(app.root_path, 'static/results', file_filename)
    form_file.save(file_path)
    
    return file_filename


@app.route("/dashboard")
@login_required
def dashboard():
    message = motd.query.order_by(motd.date.desc()).first()
    page = request.args.get('page', 1, type=int)
    medcases = medcase.query.order_by(medcase.date.desc()).paginate(per_page=100, page=page)
    return render_template('dashboard.html', title='Dashboard', motd=message, medcases=medcases)



#ACCOUNT PAGES
    
#ACCOUNT PAGE
@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form=UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            image_file = save_picture(form.picture.data)
            current_user.image_file = image_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated.', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='images/profiles/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)

#ACCOUNT PASSWORD CHANGE
@app.route("/change_password", methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user = current_user
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            hashed_password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
            user.password = hashed_password
            db.session.commit()
            flash(f'Password successfully changed for {current_user.username}!', 'success')
            return redirect(url_for('account'))
        else:
            flash('Incorrect current password. Please check your password', 'danger')
    return render_template('change_password.html', title='Change Password', form=form)

@app.route("/rtctest")
def rtctest():
    return render_template('rtctest.html', title='Video Call Test')




#USER AUTHENTICATION PAGES

#REGISTRATION PAGE
@app.route("/register", methods=['GET', 'POST'])
def register():
#    if current_user.is_authenticated:
#        return redirect(url_for('home'))
    available_roles=db.session.query(UserRole).all()
    role_list=[(UserRole.id, UserRole.name) for UserRole in available_roles]
    form = RegistrationForm()
    form.role.choices = role_list
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, role=form.role.data, blocked=0)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}! You are now able to log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Registration', form=form)

#LOGIN PAGE
@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            user.last_login=datetime.utcnow()
            db.session.commit()
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect (next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

#LOGOUT CONTROL
@app.route("/logout")
def logout():
    logout_user()
    flash('You are now logged out.', 'primary')
    return redirect(url_for('home'))

#PASSWORD RESET REQUEST PAGE
@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
            flash('An email has been sent with instructions to reset your password.', 'info')
            return redirect(url_for('login'))
        else:
            flash('The entered account does not exist. Please check your email address.', 'danger')
    return render_template('reset_request.html', title='Reset Password', form=form)

#PASSWORD RESET (TOKEN ONLY) PAGE
@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user= User.verify_reset_token(token)
    if not user:
        flash('The reset token is invalid or expired.', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash(f'Password reset for has been updated! You are now able to log in.', 'success')
        return redirect(url_for('login'))    
    return render_template('reset_token.html', title='Reset Password', form=form)



#POST PAGES

#POST DATAGRID
@app.route("/posts")
def posts():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(per_page=100, page=page)
    return render_template('posts.html', title='Posts', posts=posts)

#NEW POST FORM
@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.postcontent.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('posts'))
    return render_template('post_new.html', title = "New Post", 
                           legend='New Post', form=form)

#SINGLE POST PAGE
@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
@login_required
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)

#POST UPDATE PAGE
@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.postcontent.data
        db.session.commit()
        flash('Your post has been edited.', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.postcontent.data = post.content        
    return render_template('post_new.html', title='Update Post', 
                           legend='Update Post', form=form)

#POST DELETE CONTROL
@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted.', 'info')
    return redirect(url_for('home'))

#SINGLE ACCOUNT VIEW
@app.route("/user/<string:username>")
def user_post(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(per_page=3, page=page)
    return render_template('user_post.html', posts=posts, user=user, title="{% user%}'s Posts")


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', 
                  sender='noreply@mediconsult.com', 
                  recipients=[user.email])
    msg.body = f'''To reset your password, click on the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request, simply ignore this email and no changes will be made.
'''
    mail.send(msg)


#ADMIN PAGES
#User DATAGRID
@app.route("/admin/users")
@login_required
def admin_users():
    if current_user.role != 1:
        abort(403)
    page = request.args.get('page', 1, type=int)
    user = User.query.paginate(per_page=100, page=page)
    return render_template('admin_users.html', title='Posts', user=user)

#MESSAGE OF THE DAY CONTROLS
@app.route("/admin/motd", methods=['GET', 'POST'])
@login_required
def admin_motd():
    form = MOTDForm()
    page = request.args.get('page', 1, type=int)
    motdpreview = motd.query.order_by(motd.date.desc()).first()
    motds = motd.query.order_by(motd.date.desc()).paginate(per_page=100, page=page)
    if form.validate_on_submit():
        post = motd(title=form.title.data, content=form.motdcontent.data, sender=current_user)
        db.session.add(post)
        db.session.commit()
        flash('New Message of The Day has been sent!', 'success')
        return redirect(url_for('admin_motd'))
    
    return render_template('admin_motd.html', title = "MOTD", 
                           legend='New MOTD Message', form=form, motds=motds, motd=motdpreview)

#MOTD DELETE CONTROL
@app.route("/admin/motd/<int:motd_id>/delete", methods=['POST'])
@login_required
def delete_motd(motd_id):
    message = motd.query.get_or_404(motd_id)
    db.session.delete(message)
    db.session.commit()
    flash('MOTD has been deleted.', 'info')
    return redirect(url_for('admin_motd'))

#ADMIN ACCOUNT PAGE
@app.route("/admin/account/<string:username>", methods=['GET', 'POST'])
@login_required
def admin_account(username):
    user = User.query.filter_by(username=username).first_or_404()
    form=UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            image_file = save_picture(form.picture.data)
            user.image_file = image_file
        user.username = form.username.data
        user.email = form.email.data
        db.session.commit()
        flash('The account has been updated.', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
    image_file = url_for('static', filename='images/profiles/' + user.image_file)
    return render_template('admin_account.html', title='Account', image_file=image_file, form=form, user=user)

#Admin ACCOUNT PASSWORD CHANGE
@app.route("/admin/change_password/<string:username>", methods=['GET', 'POST'])
@login_required
def admin_change_password(username):
    form = AdminChangePasswordForm()
    user = User.query.filter_by(username=username).first_or_404()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash(f'Password successfully changed for {user.username}!', 'success')
        return redirect(url_for('admin_account', username=user.username))
    return render_template('admin_change_password.html', title='Change Password', form=form, user=user)

#USER PATIENT LIST
@app.route("/mypatients", methods=['GET', 'POST'])
@login_required
def mypatients():
    page = request.args.get('page', 1, type=int)
    patients = Patient.query.order_by(Patient.name.desc()).paginate(per_page=100, page=page)

    return render_template('mypatients.html', title = "My Patients", 
                           legend='New MOTD Message', patients=patients)

#NEW PATIENT PAGE
@app.route("/mypatients/new", methods=['GET', 'POST'])
@login_required
def new_patient():
    form = NewPatientForm()
    if form.validate_on_submit():
        patient = Patient(name=form.name.data, dob=form.dob.data, gender=form.gender.data, 
						address=form.address.data, contact_no=form.contact_no.data, carer=current_user)
        db.session.add(patient)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('mypatients'))
    return render_template('mypatient_new.html', title = "New Patient", 
                           legend='Register a New Patient', form=form)

#ADMIN PATIENTS DATAGRID
@app.route("/admin/patients")
@login_required
def admin_patients():
    page = request.args.get('page', 1, type=int)
    patients = Patient.query.paginate(per_page=100, page=page)
    return render_template('admin_patients.html', title='Patients', patients=patients)

#PATIENT DELETE CONTROL
@app.route("/admin/patient/<int:patient_id>/delete", methods=['POST'])
@login_required
def delete_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    db.session.delete(patient)
    db.session.commit()
    flash('The patient has been deleted.', 'info')
    return redirect(url_for('admin_patients'))

#CASES DATAGRID
@app.route("/cases")
@login_required
def cases():
    page = request.args.get('page', 1, type=int)
    medcases = medcase.query.order_by(medcase.date.desc()).paginate(per_page=100, page=page)
    return render_template('medcases.html', title='Cases', medcases=medcases)

#ADMIN CASES DATAGRID
@app.route("/admin/cases")
@login_required
def admin_cases():
    page = request.args.get('page', 1, type=int)
    medcases = medcase.query.order_by(medcase.date.desc()).paginate(per_page=100, page=page)
    return render_template('admin_cases.html', title='Cases', medcases=medcases)

#CASE DELETE CONTROL
@app.route("/admin/cases/<int:medcase_id>/delete", methods=['POST'])
@login_required
def delete_case(medcase_id):
    case = medcase.query.get_or_404(medcase_id)
    db.session.delete(case)
    db.session.commit()
    flash('The case has been deleted.', 'info')
    return redirect(url_for('admin_cases'))


#NEW CASES PAGE
@app.route("/cases/new", methods=['GET', 'POST'])
@login_required
def new_case():
    available_patients=db.session.query(Patient).filter(Patient.user_id == current_user.id).all()
    patient_list=[(patient.id, patient.name) for patient in available_patients]
    form = NewCaseForm()
    form.patient.choices = patient_list
    if form.validate_on_submit():
        case = medcase(patient_id=form.patient.data, title=form.title.data, content=form.casecontent.data, poster=current_user)
        db.session.add(case)
        db.session.commit()
        flash('Your case has been created!', 'success')
        return redirect(url_for('cases'))
    return render_template('cases_new.html', title = "New Case", 
                           legend='Create a New Case', form=form)

#SINGLE MedCase PAGE
@app.route("/cases/<int:case_id>", methods=['GET', 'POST'])
@login_required
def case(case_id):
    case = medcase.query.get_or_404(case_id)
    patient = Patient.query.get_or_404(case.patient_id)
    page = request.args.get('page', 1, type=int)
    comments = Comment.query.order_by(Comment.date.desc()).paginate(per_page=2, page=page)
    form = CommentForm()
    if form.validate_on_submit():
        postcomment = Comment(content=form.commentcontent.data, commenter=current_user, medcase_id=case.id)
        db.session.add(postcomment)
        db.session.commit()
        flash('Your comment has been posted.', 'success')
        return redirect(url_for('case', case_id=case.id, title=case.title, case=case, patient=patient, comments=comments, form=form))
    return render_template('medcase.html', title=case.title, case=case, patient=patient, comments=comments, form=form)

#PATIENT Detail PAGE
@app.route("/patient/<int:patient_id>/update", methods=['GET', 'POST'])
@login_required
def patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    patient_history = History.query.get(patient_id)
    page = request.args.get('page', 1, type=int)
    notes = PatientNotes.query.filter_by(notepatient=patient).order_by(PatientNotes.date.desc()).paginate(per_page=100, page=page)
    referrals = Referral.query.filter_by(referralpatient=patient).order_by(Referral.date.desc()).paginate(per_page=100, page=page)
    results = Result.query.filter_by(resultpatient=patient).order_by(Result.date.desc()).paginate(per_page=100, page=page)
    prescriptions = Prescription.query.filter_by(prescribedto=patient).order_by(Prescription.date.desc()).paginate(per_page=100, page=page)
    log = Accesshistory(user=current_user, viewed=patient)
    db.session.add(log)
    db.session.commit()
    if patient.carer != current_user:
        abort(403)
    form = NewPatientForm()
    if form.validate_on_submit():
        patient.name = form.name.data
        patient.dob = form.dob.data
        patient.gender = form.gender.data
        patient.address = form.address.data
        patient.contact_no = form.contact_no.data
        db.session.commit()
        flash('Your patient has been edited.', 'success')
        return redirect(url_for('patient', patient_id=patient.id))
    elif request.method == 'GET':
        form.name.data = patient.name
        form.dob.data = patient.dob
        form.gender.data = patient.gender
        form.address.data = patient.address
        form.contact_no.data = patient.contact_no
    hform = HistoryForm()
    if patient_history:
        if hform.validate_on_submit():
            History.general = hform.general.data
            History.medical = hform.medical.data
            History.family = hform.family.data
            History.personal = hform.personal.data
            db.session.commit()
            flash('Your patient has been edited.', 'success')
            return redirect(url_for('patient', patient_id=patient.id))
        elif request.method == 'GET':
            hform.general.data = patient_history.general
            hform.medical.data = patient_history.medical
            hform.family.data = patient_history.family
            hform.personal.data = patient_history.personal
    return render_template('patient.html', title='Patient Details', 
                           legend='Patient Details', form=form, hform=hform, patient_history=patient_history,
                           patient=patient, notes=notes, referrals=referrals, 
                           results=results, prescriptions=prescriptions)

#NEW HISTORY FORM
@app.route("/patient/history/<int:patient_id>", methods=['GET', 'POST'])
@login_required
def new_history(patient_id):
    form = HistoryForm()
    patient = Patient.query.get_or_404(patient_id)
    if form.validate_on_submit():
        note = History(general=form.general.data, medical=form.medical.data, 
						family=form.family.data, personal=form.personal.data, 
						historyowner=patient)
        db.session.add(note)
        db.session.commit()
        flash('Patient history has been created!', 'success')
        return redirect(url_for('patient', patient_id=patient.id))
    return render_template('history_new.html', title = "New history", 
                           legend='New history', form=form)

#NEW PRESCRIPTION FORM
@app.route("/new_prescription/<int:patient_id>", methods=['GET', 'POST'])
@login_required
def new_prescription(patient_id):
    form = PrescriptionForm()
    patient = Patient.query.get_or_404(patient_id)
    if form.validate_on_submit():
        pres = Prescription(medication=form.medication.data, frequency=form.frequency.data, 
							period=form.period.data, comment=form.comment.data, prescribedto=patient, 
							prescribedby=current_user, date=datetime.utcnow,)
        db.session.add(pres)
        db.session.commit()
        flash('Your prescription has been created!', 'success')
        return redirect(url_for('patient', patient_id=patient.id))
    return render_template('prescription_new.html', title = "New Prescription", 
                           legend='New Prescription', form=form)

#NEW Note FORM
@app.route("/newnote/<int:patient_id>", methods=['GET', 'POST'])
@login_required
def new_note(patient_id):
    form = NoteForm()
    patient = Patient.query.get_or_404(patient_id)
    if form.validate_on_submit():
        note = PatientNotes(title=form.title.data, content=form.notecontent.data, 
                            notewriter=current_user, notepatient=patient)
        db.session.add(note)
        db.session.commit()
        flash('Your note has been created!', 'success')
        return redirect(url_for('patient', patient_id=patient.id))
    return render_template('note_new.html', title = "New Note", 
                           legend='New Note', form=form)

#Access History Page
@app.route("/admin/accesshistory")
@login_required
def access_history():
    page = request.args.get('page', 1, type=int)
    lists = Accesshistory.query.order_by(Accesshistory.date.desc()).paginate(per_page=100, page=page)
    return render_template('admin_accesshistory.html', title = "User Access History", 
                           legend='User Access History', lists=lists)

#ADD NEW RESULT PAGE
@app.route("/patient/<int:patient_id>/result/new", methods=['GET', 'POST'])
@login_required
def result_new(patient_id):
    form=ResultForm()
    patient = Patient.query.get_or_404(patient_id)
    if form.validate_on_submit():
        result_file = save_file(form.file.data)
        entry = Result(comment=form.comment.data, result_file=result_file, resultpatient=patient, resultuser=current_user)
        db.session.add(entry)
        db.session.commit()
        flash('Your file has been uploaded.', 'success')
        return redirect(url_for('contact'))
    return render_template('result_new.html', title='New Result', form=form)

#Video Call PAGE
@app.route("/rtc")
def rtc():
    return render_template('rtc.html', title='RTC')

#CHAT PAGE
@app.route("/chat")
@login_required
def chat():
    return render_template('chat.html', title='Chat', user=current_user)


def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')


@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    print('received my event: ' + str(json))
    socketio.emit('my response', json, callback=messageReceived)
