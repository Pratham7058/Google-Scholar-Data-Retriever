from flask import render_template, redirect, url_for, flash, request, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Profile
from forms import RegistrationForm, LoginForm, ProfileForm
from generate_all import generate_excel_file
from bson.objectid import ObjectId
import os

def register_routes(app):
    @app.route('/', methods=['GET', 'POST'])
    def base():
        return render_template('base2.html')
    
    @app.route('/base2')
    def base2():
        return render_template('base2.html')
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(
                username=form.username.data,
                email=form.email.data,
                password=generate_password_hash(form.password.data, method='sha256')
            )
            user.save()
            flash('You have successfully registered! You can now log in.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html', form=form, current_user=current_user)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = User.objects(username=form.username.data).first()
            if user and check_password_hash(user.password, form.password.data):
                login_user(user)
                flash('You have been logged in!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Login unsuccessful. Please check your username and password.', 'danger')
        return render_template('login.html', form=form,current_user=current_user)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'success')
        return redirect(url_for('login'))

    @app.route('/dashboard', methods=['GET', 'POST'])
    @login_required
    def dashboard():
        form = ProfileForm()
        if form.validate_on_submit():
            profile = Profile(
                name=form.name.data,
                query=form.query.data,
                owner_id=ObjectId(current_user.id)
            )
            profile.save()
            current_user.update(push__profiles=profile)
            flash('Profile added successfully!', 'success')
            return redirect(url_for('dashboard'))
        profiles = current_user.profiles
        return render_template('dashboard.html', form=form, profiles=profiles)

    @app.route('/generate_excel/<profile_id>')
    @login_required
    def generate_excel(profile_id):
        profile = Profile.objects.get(id=profile_id)
        if profile.owner_id != current_user.id:
            flash('You are not authorized to access this profile.', 'danger')
            return redirect(url_for('dashboard'))

        # Call the function from the extract.py file
        excel_path = generate_excel_file(profile.query)
        profile.update(set__generated_excel_path=excel_path)

        return redirect(url_for('download_excel', profile_id=profile_id))

    @app.route('/download_excel/<profile_id>')
    @login_required
    def download_excel(profile_id):
        profile = Profile.objects.get(id=profile_id)
        if profile.owner_id != current_user.id:
            flash('You are not authorized to access this profile.', 'danger')
            return redirect(url_for('dashboard'))

        return send_file(profile.generated_excel_path, as_attachment=True)
    
    @app.route('/delete_profile/<profile_id>', methods=['GET', 'POST'])
    @login_required
    def delete_profile(profile_id):
        profile = Profile.objects.get(id=profile_id)
        if profile.owner_id != current_user.id:
           flash('You are not authorized to delete this profile.', 'danger')
           return redirect(url_for('dashboard'))

    # Delete the associated Excel file if it exists
        if profile.generated_excel_path:
           try:
              os.remove(profile.generated_excel_path)
           except OSError as e:
              print(f"Error deleting file: {e}")

    # Remove the profile from the user's profile list
        current_user.update(pull__profiles=profile)

    # Delete the profile document
        profile.delete()

        flash('Profile deleted successfully.', 'success')
        return redirect(url_for('dashboard'))