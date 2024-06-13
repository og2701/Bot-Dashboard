from flask import Blueprint, render_template, request, redirect, url_for, session, current_app

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        print(current_app.config['LOGIN_PASSWORD'])
        print("PASSWORD ^")
        if password == current_app.config['LOGIN_PASSWORD']:
            session['logged_in'] = True
            return redirect(url_for('main.index'))
        else:
            return render_template('login.html', error='Invalid password')
    return render_template('login.html')

@auth.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('auth.login'))
