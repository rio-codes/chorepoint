from flask import Flask, flash, render_template, request, redirect, url_for, session
from flask_login import current_user, logout_user, LoginManager, login_user, login_required
from flask_mail import Mail, Message
from flask_mysqldb import MySQL
from flask_appconfig.heroku import from_heroku_envvars
import MySQLdb
from datetime import datetime, timedelta
import hashlib, random, string, jwt, time, re, os
from config import *

app = Flask(__name__)

is_prod = os.environ.get('IS_HEROKU', None)

if is_prod:
    app.config.from_object('ProdConfig')
else:
    app.config.from_envvar("CHOREPOINT_SETTINGS")

print(app.config.get('MYSQL_HOST'))

mysql = MySQL(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
mail = Mail(app)

class User(object):
    def __init__(self, userID, username, displayName, admin, passwordHash, approvalRequired, points, homeID, is_authenticated, is_active, is_anonymous, email):
        self.userID = userID
        self.username = username
        self.displayName = displayName
        self.admin = admin
        self.passwordHash = passwordHash
        self.approvalRequired = approvalRequired
        self.points = points
        self.homeID = homeID
        self.is_active = is_active
        self.is_anonymous = is_anonymous
        self.email = email

    def is_authenticated(self):
        return True

    @classmethod

    def get_user(self, userID):

        # initialize userID variable and mysql cursor
        u = (userID,)
        cur = mysql.connection.cursor()

        # get user for userID
        cur.execute("SELECT * FROM users WHERE userID=%s", u)
        columns = [col[0] for col in cur.description]
        user = [dict(zip(columns, row)) for row in cur.fetchall()]

        # return user object
        if user == []:
            return None
        else :
            return User(user[0]['userID'],user[0]['username'],user[0]['displayName'],user[0]['admin'],user[0]['passwordHash'],user[0]['approvalRequired'],user[0]['points'],user[0]['homeID'],user[0]['is_authenticated'],user[0]['is_active'],user[0]['is_anonymous'],user[0]['email'])

    def get_userID_from_username(username):

        # initialize username variable and mysql cursor
        u = (username,)
        cur = mysql.connection.cursor()

        # get userID for username
        cur.execute("SELECT userID FROM users WHERE username=%s", u)
        userTuple = cur.fetchall()
        print(userTuple)
        if userTuple != ():
            user = int(((userTuple[0])[0]))
        else:
            user = False

        # return userID
        return user
    
    def get_userID_from_email(email):

        # initialize username variable and mysql cursor
        e = (email,)
        cur = mysql.connection.cursor()

        # get userID for username
        cur.execute("SELECT userID FROM users WHERE email=%s", e)
        userTuple = cur.fetchall()
        user = int(((userTuple[0])[0]))

        # return userID
        return user

    def get_home_users(homeID):

        # initialize homeID variable and mysql cursor
        h = (homeID,)
        cur = mysql.connection.cursor()

        # get userIDs for homeID
        cur.execute("SELECT userID FROM users WHERE homeID=%s AND is_active=1", h)

        # return userIDs
        users = cur.fetchall()
        return users
    
    def add_points(userID, points):

        # initialize user variable and sql cursor
        u = (userID,)
        cur = mysql.connection.cursor()
        
        # get current points for selected user
        cur.execute("SELECT points FROM users WHERE userID=%s", u)
        currentPoints = (cur.fetchall()[0])[0]

        # generate new point total
        newPoints = currentPoints + int(points)

        # add points to user
        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET points=%s WHERE userID=%s" % (newPoints, userID))
        mysql.connection.commit()

    def subtract_points(userID, points):

        # initialize user variable and sql cursor
        u = (userID,)
        cur = mysql.connection.cursor()
        
        # get current points for selected user
        cur.execute("SELECT points FROM users WHERE userID=%s", u)
        currentPoints = (cur.fetchall()[0])[0]

        # generate new point total
        newPoints = currentPoints - int(points)

        # add points to user
        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET points=%s WHERE userID=%s" % (newPoints, userID))
        mysql.connection.commit()

    def get_id(self):
        print("get id")
        userID = self.userID
        # return unicode user ID
        return userID
    
    def create_new_user(username, displayName, homeName, pw_hash, email):

        # get last userID and create new userID
        cur = mysql.connection.cursor()
        cur.execute("SELECT userID FROM users ORDER BY userID DESC LIMIT 1")
        lastUserID = cur.fetchall()[0]
        newUserID = int((lastUserID[0])) + 1

        # get next homeID
        cur = mysql.connection.cursor()
        cur.execute("SELECT homeID FROM homes ORDER BY homeID DESC LIMIT 1")
        lastHomeID = cur.fetchall()[0]
        newHomeID = int((lastHomeID[0])) + 1

        # generate invite link
        invite = Home.generate_invite_link()

        # add new home to database
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO homes (homeID, homeName, adminUserID, inviteLink) VALUES (%s, %s, %s, %s)", (newHomeID, homeName, newUserID, invite))
        mysql.connection.commit()

        # add new user to database
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (userID, username, displayName, admin, passwordHash, approvalRequired, points, homeID, email) VALUES (%s, %s, %s, 1, %s, 0, 0, %s, %s)", (newUserID, username, displayName, pw_hash, newHomeID, email))
        mysql.connection.commit()
    
    def create_new_invited_user(username, displayName, homeID, pw_hash):

        # get last userID and create new userID
        cur = mysql.connection.cursor()
        cur.execute("SELECT userID FROM users ORDER BY userID DESC LIMIT 1")
        lastUserID = cur.fetchall()[0]
        newUserID = int((lastUserID[0])) + 1

        # add new user to database
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (userID, username, displayName, admin, passwordHash, approvalRequired, points, homeID) VALUES (%s, '%s', '%s', 0, '%s', 1, 0, %s)" % (newUserID, username, displayName, pw_hash, homeID))
        mysql.connection.commit()

    def change_password(userID, pw_hash):

        print(pw_hash)
        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET passwordHash='%s' WHERE userID = %s" % (pw_hash, userID))
        mysql.connection.commit()

    def promote_user(userID, newUsername):

        # get current user object and home object
        user = User.get_user(userID)
        home = Home.get_home_from_homeID(user.homeID)

        # create new user with admin status and no approval required and get user object
        User.create_new_user(newUsername, user.displayName, home.homeName, user.passwordHash)
        newUserID = User.get_userID_from_username(newUsername)
        newUser = User.get_user(newUserID)

        # get new homeID
        newHome = Home.get_home_from_homeID(newUser.homeID)

        # change all tasks to new user and homeID
        cur = mysql.connection.cursor()
        cur.execute("UPDATE tasks SET assignedUserID=%s, homeID=%s WHERE assignedUserID = %s" % (newUserID, newHome.homeID, user.userID))
        mysql.connection.commit()
        
        # set all active tasks to uncompleted
        cur = mysql.connection.cursor()
        cur.execute("UPDATE tasks SET approved=0 WHERE assignedUserID = %s AND active=1" % (newUserID))
        mysql.connection.commit()

        # change all rewards to new user and homeID
        cur = mysql.connection.cursor()
        cur.execute("UPDATE rewards SET assignedUserID=%s, homeID=%s WHERE assignedUserID = %s" % (newUserID, newHome.homeID, user.userID))
        mysql.connection.commit()

        # deactivate old user
        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET is_authenticated=0, is_active=0 WHERE userID = %s" % (user.userID))
        mysql.connection.commit()

    def delete_user(userID):

        #deactivate user
        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET is_authenticated=0, is_active=0 WHERE userID = %s" % (userID))
        mysql.connection.commit()

    def send_reset_email(user):

        token = user.get_reset_token()

        msg = Message()
        msg.subject = "Chorepoint Password Reset"
        msg.sender = os.environ.get('MAIL_USERNAME')
        msg.recipients = [user.email]
        msg.html = render_template('reset_email.html',
                                user=user, 
                                token=token)
        mail.send(msg)

    def get_reset_token(self, expires=500):
        key = os.environ.get('SECRET_KEY')
        return jwt.encode({'reset_password': self.username,
                           'exp': time.time() + expires},
                           key, algorithm="HS256")

class Task(object):
    def __init__(self, taskID, taskName, points, approved, assignedUserID, createdByUserID, dateCreated, dateCompleted, frequency, dueDate, homeID, assignedUsername, active, permanent):
        self.taskID = taskID
        self.taskName = taskName
        self.points = points
        self.approved = approved
        self.assignedUserID = assignedUserID
        self.createdByUserID = createdByUserID
        self.dateCreated = dateCreated
        self.dateCompleted = dateCompleted
        self.frequency = frequency
        self.dueDate = dueDate
        self.homeID = homeID
        self.assignedUsername = assignedUsername
        self.active = active
        self.permanent = permanent

    def get_task(taskID):

        # initialize task variable and mysql cursor
        t = (taskID,)
        cur = mysql.connection.cursor()

        # get task for taskID
        cur.execute("SELECT * FROM tasks WHERE taskID=%s", t)
        columns = [col[0] for col in cur.description]
        task = [dict(zip(columns, row)) for row in cur.fetchall()]

        # get assigned user for task
        assignedUser = User.get_user(task[0]['assignedUserID'])
        assignedUsername = assignedUser.username

        # return Task object
        return Task(taskID, task[0]['taskName'], task[0]['points'],  task[0]['approved'], task[0]['assignedUserID'], task[0]['createdByUserID'], task[0]['dateCreated'], task[0]['dateCompleted'], task[0]['frequency'], task[0]['dueDate'], task[0]['homeID'], assignedUsername, task[0]['active'], task[0]['permanent'])

    def get_home_tasks(homeID):

        # initialize home variable and mysql cursor
        h = (homeID,)
        cur = mysql.connection.cursor()

        # get taskIDs for homeID
        cur.execute("SELECT taskID FROM tasks WHERE homeID=%s", h)
        tasks = cur.fetchall()

        # return taskIDs
        return tasks
    
    def create_next_task(taskID):
        # get task object
        thisTask = Task.get_task(taskID)

        # initialize sql cursor
        cur = mysql.connection.cursor()

        # get last taskID and create new taskID
        cur.execute("SELECT taskID FROM tasks ORDER BY taskID DESC LIMIT 1")
        lastTaskID = cur.fetchall()[0]
        newTaskID = int((lastTaskID[0])) + 1

        # set and format current date
        currentDate = datetime.now()
        formattedDate = str(currentDate.strftime('%Y-%m-%d'))
        dateString = "%Y-%m-%d"   

        # set and format due date based on frequency
        dueDate = thisTask.dueDate + timedelta(int(thisTask.frequency))
        formattedDueDate = str(dueDate.strftime('%Y-%m-%d'))

        # intialize sql cursor
        cur = mysql.connection.cursor()

        # add new task to database
        cur.execute("INSERT INTO tasks (taskID, taskName, points, approved, assignedUserID, createdByUserID, dateCreated, frequency, dueDate, homeID, active, permanent) SELECT %s, taskName, points, 0, assignedUserID, createdByUserID, STR_TO_DATE('%s','%s'), frequency, STR_TO_DATE('%s','%s'), homeID, 1, permanent FROM tasks WHERE taskID=%s" % (newTaskID, formattedDate, dateString, formattedDueDate, dateString, taskID))
        mysql.connection.commit()
    
    def create_new_task(taskName, points, assignedUserID, createdByUserID, frequency, homeID, dueDate, permanent, oneOff):

        print("after called")
        print(permanent)
        print(frequency)
        print(dueDate) 

        # initialize sql cursor
        cur = mysql.connection.cursor()

        # get last taskID and create new taskID
        cur.execute("SELECT taskID FROM tasks ORDER BY taskID DESC LIMIT 1")
        lastTaskID = cur.fetchall()[0]
        newTaskID = int((lastTaskID[0])) + 1

        # set and format current date

        
        currentDate = datetime.now()
        print(currentDate)
        formattedDate = str(currentDate.strftime('%Y-%m-%d'))
        print(formattedDate)
        dateString = "%Y-%m-%d"

        # check if task is permanent
        if dueDate == "3000-01-01" and permanent == "1":
            # add task to database
              cur.execute("INSERT INTO tasks (taskID, taskName, points, approved, assignedUserID, createdByUserID, dateCreated, frequency, dueDate, homeID, active, permanent) VALUES (%s, '%s', %s, 0, %s, %s, STR_TO_DATE('%s','%s'), %s, STR_TO_DATE('%s','%s'), %s, 1, 1)" % (newTaskID, str(taskName), points, assignedUserID, createdByUserID, formattedDate, dateString, frequency, dueDate, dateString, homeID))
              mysql.connection.commit()

        # check if task is one-off
        elif oneOff == 1:
            print(frequency)

            # add task to database due on future date
            cur.execute("INSERT INTO tasks (taskID, taskName, points, approved, assignedUserID, createdByUserID, dateCreated, frequency, dueDate, homeID, active, permanent) VALUES (%s, '%s', %s, 0, %s, %s, STR_TO_DATE('%s','%s'), %s, STR_TO_DATE('%s','%s'), %s, 1, 0)" % (newTaskID, str(taskName), points, assignedUserID, createdByUserID, formattedDate, dateString, frequency, dueDate, dateString, homeID))
            mysql.connection.commit()

        # otherwise set dueDate to current date
        else:

            # set and format current date
            currentDate = datetime.now()
            print(currentDate)
            formattedDate = str(currentDate.strftime('%Y-%m-%d'))
            dateString = "%Y-%m-%d"   

            # add task to database due today
            cur.execute("INSERT INTO tasks (taskID, taskName, points, approved, assignedUserID, createdByUserID, dateCreated, frequency, dueDate, homeID, active, permanent) VALUES (%s, '%s', %s, 0, %s, %s, STR_TO_DATE('%s','%s'), %s, STR_TO_DATE('%s','%s'), %s, 1, 0)" % (newTaskID, str(taskName), points, assignedUserID, createdByUserID, formattedDate, dateString, frequency, formattedDate, dateString, homeID))
            mysql.connection.commit()

    def get_user_tasks(userID):

        # initialize variable and mysql cursor
        u = (userID,)
        cur = mysql.connection.cursor()

        # get tasks assigned to user
        cur.execute("SELECT taskID FROM tasks WHERE assignedUserID=%s", u)
        tasks = cur.fetchall()

        # return taskIDs
        return tasks
    
    def delete_task(taskID):

        # initialize variable and mysql cursor
        cur = mysql.connection.cursor()
        t = (taskID,)
    
        # deactivate task
        cur.execute("UPDATE tasks SET active=0 WHERE taskID=%s", t)
        mysql.connection.commit()

class Home(object):
    def __init__(self, homeID, homeName, adminUserID):
        self.homeID = homeID
        self.homeName = homeName
        self.adminUserID = adminUserID

    @classmethod

    def get_home(self, adminUserID):

        # initialize userID variable and mysql cursor    
        u = (adminUserID,)
        cur = mysql.connection.cursor()

        print(u)
        # get home for admin user
        cur.execute("SELECT * FROM homes WHERE adminUserID=%s", u)
        columns = [col[0] for col in cur.description]
        home = [dict(zip(columns, row)) for row in cur.fetchall()]
        print(home)

        # return home object
        self.homeID = home[0]['homeID'] 
        self.homeName = home[0]['homeName']
        self.adminUserID = adminUserID
        self.inviteLink = home[0]['inviteLink']
        return self
    
    @classmethod

    def get_home_from_homeID(self, homeID):

        # initialize homeID variable and mysql cursor    
        h = (homeID,)
        cur = mysql.connection.cursor()

        # get home for admin user
        cur.execute("SELECT * FROM homes WHERE homeID=%s", h)
        columns = [col[0] for col in cur.description]
        home = [dict(zip(columns, row)) for row in cur.fetchall()]
        print(home)

        # return home object
        self.homeID = home[0]['homeID'] 
        self.homeName = home[0]['homeName']
        self.adminUserID = home[0]['adminUserID']
        self.inviteLink = home[0]['inviteLink']

        return self

    def generate_invite_link():

        randomString = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))
        return(randomString)

class Reward(object):
    def __init__(self, rewardID, rewardName, points, approved, assignedUserID, homeID, active):
        self.rewardID = rewardID
        self.rewardName = rewardName
        self.points = points
        self.approved = approved
        self.assignedUserID = assignedUserID
        self.homeID = homeID
        self.active = active

    def get_reward(rewardID):

        # intitialize reward variable and mysql cursor
        r = (rewardID,)
        cur = mysql.connection.cursor()

        # get reward for rewardID
        cur.execute("SELECT * FROM rewards WHERE rewardID=%s", r)
        columns = [col[0] for col in cur.description]
        reward = [dict(zip(columns, row)) for row in cur.fetchall()]

        # return Reward object
        return Reward(rewardID, reward[0]['rewardName'], reward[0]['points'], reward[0]['approved'], reward[0]['assignedUserID'], reward[0]['homeID'], reward[0]['active'])
    
    def get_home_rewards(homeID):

        # initialize homeID variable and mysql cursor
        h = (homeID,)
        cur = mysql.connection.cursor()

        # get rewardIDs for homeID
        cur.execute("SELECT rewardID FROM rewards WHERE homeID=%s", h)
        rewards = cur.fetchall()

        # return rewardIDs
        return rewards
    
    def get_user_rewards(userID):

        #initialize userID variable and mysql cursor
        u = (userID,)
        cur = mysql.connection.cursor()

        # get rewardIDs for user
        cur.execute("SELECT rewardID FROM rewards WHERE (assignedUserID=%s)", u)
        rewards = cur.fetchall()
        return rewards
    
    def create_next_reward(rewardID):

        # initialize sql cursor
        cur = mysql.connection.cursor()

        # get last rewardID and create new rewardID
        cur.execute("SELECT rewardID FROM rewards ORDER BY rewardID DESC LIMIT 1")
        lastRewardID = cur.fetchall()[0]
        newRewardID = int((lastRewardID[0])) + 1
        
        # set variables to insert into database
        r = rewardID
        n = newRewardID

        # initialize sql cursor
        cur = mysql.connection.cursor()

        # insert new reward into database
        cur.execute("INSERT INTO rewards (rewardID, rewardName, points, approved, assignedUserID, active, homeID) SELECT %s, rewardName, points, 0, assignedUserID, 1, homeID FROM rewards WHERE rewardID=%s" % (n, r))
        mysql.connection.commit()
    
    def create_new_reward(rewardName, points, assignedUserID):

        # initialize sql cursor
        cur = mysql.connection.cursor()

        # get last rewardID and create new rewardID
        cur.execute("SELECT rewardID FROM rewards ORDER BY rewardID DESC LIMIT 1")
        lastRewardID = cur.fetchall()[0]
        newRewardID = int((lastRewardID[0])) + 1

        # get homeID from userID
        user = User.get_user(assignedUserID)
        homeID = user.homeID

        # add reward to database
        cur.execute("INSERT INTO rewards (rewardID, rewardName, points, assignedUserID, approved, homeID, active) VALUES (%s, '%s', %s, %s, 0, %s, 1)" % (newRewardID, str(rewardName), points, assignedUserID,  homeID))
        mysql.connection.commit()

@login_manager.user_loader
def load_user(userID):
    print("load_user")
    try:
        user = User.get_user(userID)
        print(user.username)
        return User.get_user(userID)
    except:
        return None

def verify_reset_token(token):

    key = os.environ.get('SECRET_KEY')

    username = jwt.decode(token, key, algorithms="HS256")['reset_password']
    print ("VERIFYING TOKEN")

    userID = User.get_userID_from_username(username)

    return userID

def validateRegistration(displayName, username, homeName, password, email, confirm):

    s = os.environ.get('SALT')
    isValid = dict()
    isValid['error'] = None


    if displayName.strip().isdigit():
        print('name is digit')
        isValid['error'] = 'Your name cannot be a number'
        isValid['displayNameString'] = 'invalid'
        isValid['usernameString'] = None
        isValid['homeNameString'] = None
        isValid['pw_hash'] = None
        isValid['emailString'] = None
        return isValid
    else:
        isValid['displayNameString'] = MySQLdb.escape_string(displayName)
    
    isValid['usernameString'] = MySQLdb.escape_string(username)
    if isValid['usernameString'].strip().isdigit():
        print('un is digit')
        isValid['error']  = 'Your username cannot be a number'
        isValid['usernameString'] = 'invalid'
        isValid['displayNameString'] = None
        isValid['homeNameString'] = None
        isValid['pw_hash'] = None
        isValid['emailString'] = None
        return isValid
    else:
        isValid['usernameString'] = MySQLdb.escape_string(username)
        print (isValid['usernameString'])
        isUser = User.get_userID_from_username(isValid['usernameString'])
        print(isUser)
        if isUser != False:
            isValid['error']  = 'That username is taken'
            isValid['usernameString'] = 'invalid'
            isValid['displayNameString'] = 'invalid'
            isValid['usernameString'] = None
            isValid['homeNameString'] = None
            isValid['pw_hash'] = None
            isValid['emailString'] = None
            return isValid

    
    if homeName.strip().isdigit():
        isValid['error']  = 'Your home name cannot be a number'
        isValid['homeNameString'] = 'invalid'
        isValid['displayNameString'] = None
        isValid['usernameString'] = None
        isValid['pw_hash'] = None
        isValid['emailString'] = None
        return isValid
    else:
        isValid['homeNameString'] = MySQLdb.escape_string(homeName)

    passwordRegex = re.compile('[@_!#$%^&*()<>?/\|}{~:]')
    emailRegex = re.compile('^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$')

    if (any(x.isupper() for x in password) 
        and any(x.islower() for x in password) 
        and any(x.isdigit() for x in password) 
        and len(password) >= 10 
        and re.search(passwordRegex, password) != None): 
            pw = (s + password).encode()
            print (pw)
            isValid['pw_hash'] = hashlib.sha512(pw).hexdigest()
    else:
            isValid['error'] = 'Your password must be at least 10 characters long and contain an uppercase letter, a lowercase letter, and a symbol.'
            isValid['pw_hash'] = 'invalid'
            isValid['displayNameString'] = 'invalid'
            isValid['usernameString'] = None
            isValid['homeNameString'] = None
            isValid['emailString'] = None
            return isValid
    
    if (re.search(emailRegex,email)):
        isValid['emailString'] = MySQLdb.escape_string(email) 
    else:
        isValid['error'] = 'Please enter a valid email address.'
        isValid['emailString'] = 'invalid'
        isValid['displayNameString'] = None
        isValid['usernameString'] = None
        isValid['homeNameString'] = None
        isValid['pw_hash'] = None
        return isValid
    
    if password != confirm:
        isValid['error'] = 'Passwords do not match.'
        isValid['pw_hash'] = 'invalid'
        isValid['displayNameString'] = None
        isValid['usernameString'] = None
        isValid['homeNameString'] = None
        isValid['pw_hash'] = None
        isValid['emailString'] = None
        return isValid
    
    return isValid

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/bootstrap.min.css")
def bootstrap_css():
    return render_template('bootstrap.min.css')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    s = os.environ.get('SALT')

    if request.method == "POST":

        # get username and password from form
        username = request.form['username']
        password = request.form['password']

        if not username.strip().isdigit():
            usernameString = MySQLdb.escape_string(username)
        else:
            error = 'Incorrect username.'
            return render_template('login.html', error=error)

        pw = (s + password).encode()
        pw_hash = hashlib.sha512(pw).hexdigest()

        # get userID and User object
        
        userID = User.get_userID_from_username(usernameString)

        if userID == None:
            error = 'Incorrect username and/or password.'
            return render_template('login.html', error=error)
        else:
            user = User.get_user(userID)
            
        if user.passwordHash != pw_hash:    
            error = 'Incorrect password.'
            return render_template('login.html', error=error)
        else:
            # initialize login session
            
            userIDTuple = (user.userID,)
            cur = mysql.connection.cursor()
            cur.execute("UPDATE users SET is_authenticated=1 WHERE userID=%s", userIDTuple )
            mysql.connection.commit()
            
            login_user(user)
            session['userID'] = 'userID'

            # send user to correct page
            if user.admin == 1:
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('user'))

    if request.method == "GET":

        # display login page
        return render_template('login.html', error=error)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == "GET":
        user = current_user
        logout_user()
        # display login page
        return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin():
    # get current logged in user
    # userID = session['userID']    
    adminUser = current_user

    # get current home
    home = Home.get_home(adminUser.userID)

    print(home.homeID)

    # get tasks data for current home
    homeTasks = []
    homeTasksTuple = Task.get_home_tasks(home.homeID)
    for a in range(len(homeTasksTuple)):
        homeTasks.append(int(((homeTasksTuple[a])[0])))
    
    # get active and pending tasks and add to output
    allTasks=[]
    pendingTasks=[]
    for b in range(len(homeTasks)):
        thisTask = Task.get_task(homeTasks[b]) 
        if thisTask.approved == 0 and thisTask.active == 1:
            allTasks.append(thisTask)
        elif thisTask.approved == 1 and thisTask.active ==1:
            pendingTasks.append(thisTask)
    
    print(pendingTasks)
    # get rewards data for current home
    homeRewards=[]
    homeRewardsTuple = Reward.get_home_rewards(home.homeID)
    for c in range(len(homeRewardsTuple)):
        homeRewards.append(int(((homeRewardsTuple[c])[0])))
    
    # get active and pending rewards and add to output
    allRewards=[]
    pendingRewards=[]
    for d in range(len(homeRewards)):
        thisReward = Reward.get_reward(homeRewards[d])
        if thisReward.approved == 0 and thisReward.active==1:
            allRewards.append(thisReward)
        elif thisReward.approved == 1 and thisReward.active==1:
            pendingRewards.append(thisReward)

    # get users for current home
    homeUsers=[]
    homeUsersTuple = User.get_home_users(home.homeID)
    print(homeUsersTuple)   
    for f in range(len(homeUsersTuple)):
        homeUsers.append(int(((homeUsersTuple[f])[0])))
    
    # add users to output
    allUsers=[]
    for g in range(len(homeUsers)):
        thisUser = User.get_user(homeUsers[g])
        print(thisUser.username)
        allUsers.append(thisUser)

    # display admin page with output
    return render_template('admin.html',displayName=adminUser.displayName,home=home.homeName,allTasks=allTasks,allRewards=allRewards,allUsers=allUsers,pendingTasks=pendingTasks,pendingRewards=pendingRewards,adminUser=adminUser)

@app.route('/admin/<userID>')
@login_required
def adminUser(userID):
    # get current user
    user = User.get_user(userID)

    # get tasks data for current user
    userTasks = []
    userTasksTuple = Task.get_user_tasks(user.userID)
    for a in range(len(userTasksTuple)):
        userTasks.append(int(((userTasksTuple[a])[0])))
    
    # get active and pending tasks and add to output
    allTasks=[]
    pendingTasks=[]
    for b in range(len(userTasks)):
        thisTask = Task.get_task(userTasks[b]) 
        if thisTask.approved == 0 and thisTask.active == 1:
            allTasks.append(thisTask)
        elif thisTask.approved == 1 and thisTask.active ==1:
            pendingTasks.append(thisTask)
    
    print(pendingTasks)
    # get rewards data for current user
    userRewards=[]
    userRewardsTuple = Reward.get_user_rewards(user.userID)
    for c in range(len(userRewardsTuple)):
        userRewards.append(int(((userRewardsTuple[c])[0])))
    
    # get active and pending rewards and add to output
    allRewards=[]
    pendingRewards=[]
    for d in range(len(userRewards)):
        thisReward = Reward.get_reward(userRewards[d])
        if thisReward.approved == 0 and thisReward.active==1:
            allRewards.append(thisReward)
        elif thisReward.approved == 1 and thisReward.active==1:
            pendingRewards.append(thisReward)
    
    # display admin user page with output
    return render_template('adminuser.html',displayName=user.displayName,allTasks=allTasks,allRewards=allRewards,pendingTasks=pendingTasks,pendingRewards=pendingRewards,adminUser=adminUser,user=user)

@app.route('/admin/approveReward/<rewardID>', methods=['GET', 'POST'])   
@login_required
def approveReward(rewardID):

    # initialize mysql cursor and rewardID variables
    cur = mysql.connection.cursor()
    r = (rewardID,)
    
    # approve reward
    cur.execute("UPDATE rewards SET approved=2 WHERE rewardID=%s", r)
    mysql.connection.commit()

    # create next reward
    Reward.create_next_reward(rewardID)

    # return to admin page
    return redirect(url_for('admin'))

@app.route('/admin/denyReward/<rewardID>', methods=['GET'])
@login_required
def denyReward(rewardID):

    # initialize mysql cursor and rewardID variables
    cur = mysql.connection.cursor()
    r = (rewardID,)
    
    # deny reward
    cur.execute("UPDATE rewards SET approved=0 WHERE rewardID=%s", r)
    mysql.connection.commit()

    # add points to user
    reward = Reward.get_reward(rewardID)
    User.add_points(reward.assignedUserID, reward.points)

    # return to admin page
    return redirect(url_for('admin'))

@app.route('/admin/deleteReward/<rewardID>', methods=['GET'])
@login_required
def deleteReward(rewardID):

    # initialize mysql cursor and rewardID variables
    cur = mysql.connection.cursor()
    r = (rewardID,)
    
    # deactivate reward
    cur.execute("UPDATE rewards SET active=0 WHERE rewardID=%s", r)
    mysql.connection.commit()

    # return to admin page
    return redirect(url_for('admin'))

@app.route('/admin/newreward/<userID>', methods=['GET','POST'])
@login_required
def createReward(userID):
    if request.method == "POST":

        # get current user
        user = User.get_user(userID)

        # get reward info from form and user object
        rewardName = request.form['rewardName']
        if rewardName.strip().isdigit():
            error = 'Reward name cannot be a number'
            return render_template('newreward.html',error=error)
        else:
            rewardNameString = MySQLdb.escape_string(rewardName)

        points = request.form['points']
        if not points.strip().isdigit():
            error = 'Point value must be a number'
            return render_template('newrward.html', error=error)

        homeID = user.homeID

        # create new reward
        Reward.create_new_reward(rewardNameString, points, user.userID)

        # return to admin page
        return redirect(url_for('admin'))

    if request.method == "GET":

        # display new reward page
        return render_template('newreward.html')

@app.route('/admin/approveTask/<taskID>', methods=['GET', 'POST'])   
@login_required
def approveTask(taskID):

    # initialize mysql cursor and taskID variables
    cur = mysql.connection.cursor()
    t = taskID

    task = Task.get_task(taskID)

    # get and format current date
    currentDate = datetime.now()
    formattedDate = str(currentDate.strftime('%Y-%m-%d'))
    dateString = "%Y-%m-%d"

    # add points to user
    User.add_points(task.assignedUserID, task.points)

    # approve task and update date completed
    cur.execute("UPDATE tasks SET approved=2, dateCompleted=STR_TO_DATE('%s', '%s') WHERE taskID=%s" % (formattedDate, dateString, t))
    mysql.connection.commit()

    # create new task based on frequency if not permanent
    task = Task.get_task(taskID)
    if task.permanent == 0:
        Task.create_next_task(taskID)

    # return to admin page
    return redirect(url_for('admin'))

@app.route('/admin/denyTask/<taskID>', methods=['GET', 'POST'])
@login_required
def denyTask(taskID):
    # initialize mysql cursor and taskID variables
    cur = mysql.connection.cursor()
    t = (taskID,)
    
    # deny task
    cur.execute("UPDATE tasks SET approved=0 WHERE taskID=%s", t)
    mysql.connection.commit()

    # return to admin page
    return redirect(url_for('admin'))

@app.route('/admin/deleteTask/<taskID>', methods=['GET', 'POST'])
@login_required
def deleteTask(taskID):
    
    # delete task
    Task.delete_task(taskID)

    # return to admin page
    return redirect(url_for('admin'))

@app.route('/admin/newtask', methods=['GET','POST'])
@login_required
def createTask():
    error = None
    if request.method == "POST":

        # get current user
        user = current_user

        # get task info from form and user object
        try:
            permanent = request.form['permanent']
        except:
            permanent = 0
            frequency = 0
            try:
                oneOff = request.form['oneOff']
            except:
                oneOff = 0
                frequency = request.form['frequency']
                if not frequency.strip().isdigit():
                    error = 'Frequency must be a number'
                    return render_template('newtask.html',error=error)
                else:    
                    dueDate = "3000-01-01"

        if permanent == "1":
            frequency = 0
            oneOff = 0
            dueDate = "3000-01-01"
        

        elif oneOff == "1":
                frequency = 0
                dueDate = request.form['dueDate']

        taskName = request.form['taskName']
        if taskName.strip().isdigit():
            error = 'Task name cannot be a number'
            return render_template('newtask.html',error=error)
        else:
            taskNameString = MySQLdb.escape_string(taskName)

        points = request.form['points']
        if not points.strip().isdigit():
            error = 'Point value must be a number'
            return render_template('newtask.html', error=error)
        
        assignedUserID = request.form['assignedUserID']
        createdByUserID = user.userID
        
        homeID = user.homeID

        # create new task for future date
        Task.create_new_task(taskNameString, points, assignedUserID, createdByUserID, frequency, homeID, dueDate, permanent, oneOff)

        if assignedUserID == createdByUserID:
            return redirect(url_for('self'))
        else:
            return redirect(url_for('admin/<assignedUserID>'))

    if request.method == "GET":

        # get current user
        user = current_user

        # get users for current home
        homeUsers=[]
        homeUsersTuple = User.get_home_users(user.homeID)   
        for f in range(len(homeUsersTuple)):
            homeUsers.append(int(((homeUsersTuple[f])[0])))
    
        # add users to output
        allUsers=[]
        for g in range(len(homeUsers)):
            thisUser = User.get_user(homeUsers[g])
            allUsers.append(thisUser)

        # display new task page
        return render_template('newtask.html',allUsers=allUsers)

@app.route('/user', methods=['GET', 'POST'])
@login_required
def user():

    # get user ID and create user object
    user = current_user

    # get and format current date
    currentDate = datetime.now().date()
    formattedDate = str(currentDate.strftime('%Y-%m-%d'))
    permanentDate = "3000-01-01"
    
    # get tasks for current user
    userTasks = []
    userTasksTuple = Task.get_user_tasks(user.userID)
    print(userTasksTuple)

    for a in range(len(userTasksTuple)):
        userTasks.append(int(((userTasksTuple[a])[0])))

    # initialize task arrays
    userPendingTasks = []
    userActiveTasks = []
    userCompletedTasks = []
    userUpcomingTasks = []
    
    
    # create new tasks for uncompleted tasks and delete original tasks
    for userTask in userTasks:
        thisTask = Task.get_task(userTask)

        if thisTask.approved == 0 and thisTask.dueDate < currentDate  and thisTask.active == 1:  
            print(thisTask.taskName)
            Task.create_next_task(thisTask.taskID)          
            Task.delete_task(thisTask.taskID)
            

    # fill arrays for active, pending, completed, and upcoming tasks
    for userTask in userTasks:
        thisTask = Task.get_task(userTask)
        thisDate = str(thisTask.dueDate)
        if thisTask.approved == 0  and thisTask.active == 1 and (thisDate == formattedDate or thisTask.permanent == 1):        
            userActiveTasks.append(thisTask)
        elif thisTask.approved == 1 and thisTask.active == 1:
            userPendingTasks.append(thisTask)
        elif thisTask.approved == 2  and thisTask.active ==1 and thisDate == formattedDate:
            userCompletedTasks.append(thisTask)
        elif thisTask.approved == 0  and thisTask.active == 1 and thisTask.dueDate > currentDate:
            userUpcomingTasks.append(thisTask)

    print(userTasks)

    # get rewards for current user
    userRewards = []    
    userRewardsTuple = Reward.get_user_rewards(user.userID)
    for a in range(len(userRewardsTuple)):
        userRewards.append(int(((userRewardsTuple[a])[0])))

    # initialize reward arrays
    userAvailableRewards = []
    userPendingRewards = []
    userRedeemedRewards = []

    # fill arrays for available, pending, and redeemed rewards
    for userReward in userRewards:
        thisReward = Reward.get_reward(userReward)
        if thisReward.approved == 0 and thisReward.active==1:
            userAvailableRewards.append(thisReward)
        elif thisReward.approved == 1 and thisReward.active==1:
            userPendingRewards.append(thisReward)
        elif thisReward.approved == 2 and thisReward.active==1: 
            userRedeemedRewards.append(thisReward)

    # prompt user to ask for content if there is none
    ask = 0
    if userTasks == [] and userRewards == []:
        ask = "Ask your admin to assign you tasks and rewards!"

    # display user page with resulting output
    return render_template('user.html', username = user.username, points = user.points, userActiveTasks=userActiveTasks, userPendingTasks=userPendingTasks, userCompletedTasks=userCompletedTasks, userAvailableRewards=userAvailableRewards, userPendingRewards=userPendingRewards, userRedeemedRewards=userRedeemedRewards, userUpcomingTasks=userUpcomingTasks, ask=ask)

@app.route('/user/redeem/<rewardID>')
@login_required
def redeemReward(rewardID):
    
    # initialize mysql cursor
    cur = mysql.connection.cursor()
    
    # get reward and user objects
    reward = Reward.get_reward(rewardID)
    userID = reward.assignedUserID
    user = User.get_user(userID)

    # check if user has enough points
    if user.points < reward.points:
        return redirect(url_for('notenough'))

    # subtract reward points from user's points
    newPoints = user.points - reward.points

    # initialize variables to be used in mysql queries
    n = newPoints
    r = (rewardID, )
    u = userID

    # send award for approval to admin
    cur.execute("UPDATE rewards SET approved=1 WHERE rewardID=%s;", r)
    mysql.connection.commit()

    # set new point value for user
    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET points=%s WHERE userID=%s" % (n, u))   
    mysql.connection.commit()

    # return to user page
    return redirect(url_for('user'))

@app.route('/user/submitTask/<taskID>', methods=['GET', 'POST'])
@login_required
def submitTask(taskID):
    # initialize mysql cursor, task variable, and task object
    cur = mysql.connection.cursor()
    t = (taskID,)
    task = Task.get_task(taskID)

    # send task for approval to admin
    cur.execute("UPDATE tasks SET approved=1 WHERE taskID=%s", t)
    mysql.connection.commit()

    # create new task if permanent
    if task.permanent == 1:
        Task.create_next_task(taskID)

    # return to user page
    return redirect(url_for('user'))

@app.route('/self', methods=['GET', 'POST'])
@login_required
def self():

    # get user ID and create user object
    user = current_user

    # get and format current date
    currentDate = datetime.now().date()
    formattedDate = str(currentDate.strftime('%Y-%m-%d'))
    permanentDate = "3000-01-01"
    
    # get tasks for current user
    selfTasks = []
    selfTasksTuple = Task.get_user_tasks(user.userID)
    for a in range(len(selfTasksTuple)):
        selfTasks.append(int(((selfTasksTuple[a])[0])))

    # initialize task arrays
    selfActiveTasks = []
    selfCompletedTasks = []
    selfUpcomingTasks = []
    
    # fill arrays for active, completed, and upcoming tasks
    for selfTask in selfTasks:
        thisTask = Task.get_task(selfTask)
        thisDate = str(thisTask.dueDate)
        print(thisDate == permanentDate)
        if thisTask.approved == 0  and thisTask.active == 1 and (thisDate == formattedDate or thisDate == permanentDate):        
            selfActiveTasks.append(thisTask)
        elif thisTask.approved == 2  and thisTask.active == 1:
            selfCompletedTasks.append(thisTask)
        elif thisTask.approved == 0  and thisTask.active == 1 and thisDate != formattedDate:
            selfUpcomingTasks.append(thisTask)

        # delete uncompleted tasks and create new tasks
        if thisTask.approved == 0 and thisTask.dueDate < currentDate  and thisTask.active == 1:  
            print(thisTask.taskName)
            Task.create_next_task(thisTask.taskID)          
            Task.delete_task(thisTask.taskID)

    # get rewards for current user
    selfRewards = []    
    selfRewardsTuple = Reward.get_user_rewards(user.userID)
    for a in range(len(selfRewardsTuple)):
        selfRewards.append(int(((selfRewardsTuple[a])[0])))

    # initialize reward arrays
    selfAvailableRewards = []
    selfRedeemedRewards = []

    # fill arrays for available and redeemed rewards
    for selfReward in selfRewards:
        thisReward = Reward.get_reward(selfReward)
        if thisReward.approved == 0 and thisReward.active==1:
            selfAvailableRewards.append(thisReward)
        elif thisReward.approved == 2 and thisReward.active==1: 
            selfRedeemedRewards.append(thisReward)


    # display self page with resulting output
    return render_template('self.html', username = user.username, points = user.points, selfActiveTasks=selfActiveTasks, selfCompletedTasks=selfCompletedTasks, selfUpcomingTasks=selfUpcomingTasks, selfAvailableRewards=selfAvailableRewards, selfRedeemedRewards=selfRedeemedRewards, user=user)

@app.route('/self/newtask', methods=['GET','POST'])
@login_required
def createSelfTask():
    error = None
    if request.method == "POST":

        # get current user
        user = current_user

        # get task info from form and user object
        try:
            permanent = request.form['permanent']
        except:
            permanent = 0
            frequency = 0
            try:
                oneOff = request.form['oneOff']
            except:
                oneOff = 0
                frequency = request.form['frequency']
                if not frequency.strip().isdigit():
                    error = 'Frequency must be a number'
                    return render_template('newtask.html',error=error)
                else:    
                    dueDate = "3000-01-01"

        if permanent == "1":
            frequency = 0
            oneOff = 0
            dueDate = "3000-01-01"
            print(frequency)
            print(dueDate)
        

        elif oneOff == "1":
                frequency = 0
                dueDate = request.form['dueDate']

        taskName = request.form['taskName']
        if taskName.strip().isDigit():
            error = 'Task name cannot be a number'
            return render_template('newtask.html',error=error)
        else:
            taskNameString = MySQLdb.escape_string(taskName)

        points = request.form['points']
        if not points.strip().isdigit():
            error = 'Point value must be a number'
            return render_template('newtask.html', error=error)

        assignedUserID = user.userID
        createdByUserID = user.userID
        
        homeID = user.homeID

        # create new task for future date
        Task.create_new_task(taskNameString, points, assignedUserID, createdByUserID, frequency, homeID, dueDate, permanent, oneOff)

        # return to self page
        return redirect(url_for('self'))

    if request.method == "GET":

        # get current user
        user = current_user

        allUsers = [user]

        # display new task page
        return render_template('newtask.html',allUsers=allUsers)

@app.route('/self/deleteTask/<taskID>', methods=['GET','POST'])
@login_required
def deleteSelfTask(taskID):
    
    # delete task
    Task.delete_task(taskID)

    # return to self page
    return redirect(url_for('self'))

@app.route('/self/submitTask/<taskID>', methods=['GET', 'POST'])
@login_required
def submitSelfTask(taskID):
    # initialize mysql cursor and taskID variables
    cur = mysql.connection.cursor()
    t = taskID

    task = Task.get_task(taskID)

    # get and format current date
    currentDate = datetime.now()
    formattedDate = str(currentDate.strftime('%Y-%m-%d'))
    dateString = "%Y-%m-%d"

    # add points to user
    User.add_points(task.assignedUserID, task.points)

    # automatically approve task and update date completed
    cur.execute("UPDATE tasks SET approved=2, dateCompleted=STR_TO_DATE('%s', '%s') WHERE taskID=%s" % (formattedDate, dateString, t))
    mysql.connection.commit()

    # create new task based on frequency
    task = Task.get_task(taskID)
    Task.create_next_task(taskID)

    # return to self page
    return redirect(url_for('self'))

@app.route('/self/newreward', methods=['GET','POST'])
@login_required
def createSelfReward():
    if request.method == "POST":

        # get current user
        user = current_user

        # get reward info from form and user object
        rewardName = request.form['rewardName']
        if rewardName.strip().isdigit():
            error = 'Reward name cannot be a number'
            return render_template('newreward.html',error=error)
        else:
            rewardNameString = MySQLdb.escape_string(taskName)

        points = request.form['points']
        if not points.strip().isdigit():
            error = 'Point value must be a number'
            return render_template('newtask.html', error=error)

        # create new reward
        Reward.create_new_reward(rewardNameString, points, user.userID)

        # return to admin page
        return redirect(url_for('self'))

    if request.method == "GET":

        # display new reward page
        return render_template('newreward.html')

@app.route('/self/deletereward/<rewardID>', methods=['GET','POST'])
@login_required
def selfDeleteReward():
    # initialize mysql cursor and rewardID variables
    cur = mysql.connection.cursor()
    r = (rewardID,)
    
    # deactivate reward
    cur.execute("UPDATE rewards SET active=0 WHERE rewardID=%s", r)
    mysql.connection.commit()

    # return to self page
    return redirect(url_for('self'))

@app.route('/self/redeem/<rewardID>')
@login_required
def redeemSelfReward(rewardID):
    
    # initialize mysql cursor
    cur = mysql.connection.cursor()
    
    # get reward and user objects
    reward = Reward.get_reward(rewardID)
    userID = reward.assignedUserID
    user = User.get_user(userID)

    # check if user has enough points
    if user.points < reward.points:
        return redirect(url_for('notenough'))

    # subtract reward points from user's points
    newPoints = user.points - reward.points

    # initialize variables to be used in mysql queries
    n = newPoints
    r = (rewardID, )
    u = userID

    # automatically approve reward
    cur.execute("UPDATE rewards SET approved=2 WHERE rewardID=%s;", r)
    mysql.connection.commit()

    # set new point value for user
    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET points=%s WHERE userID=%s" % (n, u))   
    mysql.connection.commit()

    # create next reward
    Reward.create_next_reward(rewardID)

    # return to self page
    return redirect(url_for('self'))

@app.route('/notenough', methods=['GET'])
@login_required
def notenough():
    if request.method == "GET":

        # get current user and points
        user = current_user
        points = user.points

        return render_template('notenough.html', points=points)

@app.route('/register', methods=["GET", "POST"])
def register():

    if request.method == "POST":

        # get input from registration form
        displayName = request.form['displayName']
        username = request.form['username']
        homeName = request.form['homeName']
        password = request.form['password']
        email = request.form['email']
        confirm = request.form['confirm']

        # if input is valid get values, otherwise return and print error

        isValid = validateRegistration(displayName, username, homeName, password, email, confirm)
        if isValid['error'] == None:
            User.create_new_user(isValid['usernameString'], isValid['displayNameString'], isValid['homeNameString'], isValid['pw_hash'], isValid['emailString'])
            print("creating new user")
            return redirect(url_for('login'))
        else:
            error = isValid['error']
            return render_template('register.html', error=error)

    if request.method == "GET":     
        # display register page
        return render_template('register.html')

@app.route('/invite/<inviteLink>', methods=["GET", "POST"])
def inviteRegister(inviteLink):
    error = None
    s = os.environ.get('SALT')

    if request.method == "POST":

        # get home
        cur = mysql.connection.cursor()
        i = (inviteLink, )
        cur.execute("SELECT adminUserID FROM homes WHERE inviteLink = %s", i)
        adminUserID = (cur.fetchall()[0])[0]
        home = Home.get_home(adminUserID)

        # get info from form
        displayName = request.form['displayName']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']
        error = None

        isValid = validateRegistration(displayName, username, home.homeName, password, email, confirm)

        if isValid['error'] == None:
            User.create_new_user(isValid['usernameString'], isValid['displayNameString'], isValid['homeNameString'], isValid['pw_hash'], isValid['emailString'])
            print("creating new user")
            return redirect(url_for('login'))
        else:
            error = isValid['error']
            return render_template('invite.html', error=error, home=home)

    if request.method == "GET":
        # get home
        cur = mysql.connection.cursor()
        i = (inviteLink, )
        cur.execute("SELECT adminUserID FROM homes WHERE inviteLink = %s", i)
        adminUserID = (cur.fetchall()[0])[0]
        print(adminUserID)
        home = Home.get_home(adminUserID)
        print("home name from object:")     
        print (home.homeName)
        user = User.get_user(adminUserID)
        # display register page
        return render_template('invite.html', error=error, user=user, home=home)

@login_required
@app.route('/admin/admininvite', methods=["GET"])
def adminInvite():

    
    # get current admin user
    adminUser = current_user
    home = Home.get_home(adminUser.userID)

    #display invite page
    return render_template('admininvite.html', home=home)

@login_required
@app.route('/admin/addpoints/<userID>', methods=["GET", "POST"])
def addUserPoints(userID):

    user = User.get_user(userID)
    error = None

    if request.method == "POST":

        # get points to add from form
        error = None
        points = request.form['points']

        if int(points) > 10000:
            error = "you can't add that many points."
            return render_template('addpoints.html', error=error)
        else:
            User.add_points(user.userID, points)
            return redirect('/admin/' + userID)
    
    if request.method == "GET":     
        # display add points page
        return render_template('addpoints.html', user=user, error=error)

@login_required
@app.route('/admin/subtractpoints/<userID>', methods=["GET", "POST"])
def subtractUserPoints(userID):

    user = User.get_user(userID)
    error = None

    if request.method == "POST":

        # get points to subtract from form
        error = None
        points = request.form['points']

        if int(points) > user.points:
            error = "you can't subtract more points than they have."
            return render_template('subtractpoints.html', user=user, error=error)

        else:
            User.subtract_points(userID, points)
            return redirect('/admin/' + userID)
    
    if request.method == "GET":     
        # display subtract points page
        return render_template('subtractpoints.html', user=user, error=error)

@login_required
@app.route('/admin/resetpassword/<userID>', methods=["GET", "POST"])
def resetPassword(userID):

    s = cfg.salt
    user = User.get_user(userID)
    error = None

    if request.method == "POST":
        password = request.form['password']
        confirm = request.form['confirm']

        if password != confirm:
            error = 'Passwords do not match.'
            return render_template('resetpassword.html', user=user, error=error)

        else:
            cur = mysql.connection.cursor()
            u = (user.username,)
            cur.execute("SELECT * FROM users WHERE username = %s", u)
            isUser = cur.fetchall()

            pw = (s + password).encode()
            pw_hash = hashlib.sha512(pw).hexdigest()

            print (pw_hash)

            User.change_password(userID, pw_hash)

            flash("Password was changed.")
            return redirect('/admin/' + userID)

    if request.method == "GET":     
        # display reset password page
        return render_template('resetpassword.html', user=user, error=error)

@login_required
@app.route('/admin/promoteuser/<userID>', methods=["GET", "POST"])
def promoteUser(userID):

    user = User.get_user(userID)
    error = None

    if request.method == "POST":

        error = None
        newUsername = request.form['username']

        cur = mysql.connection.cursor()
        u = (newUsername,)
        cur.execute("SELECT * FROM users WHERE username = %s", u)
        isUser = cur.fetchall()
        if isUser == True:
            error = 'That username is taken'
            return render_template('promoteuser.html', user=user, error=error)
        else:
            User.promote_user(userID, newUsername)
            return redirect('/admin')
    
    if request.method == "GET":

        # display promote user page
        return render_template('promoteuser.html', user=user, error=error)

@login_required
@app.route('/admin/deleteuser/<userID>', methods=["GET", "POST"])
def deleteUser(userID):
    user = User.get_user(userID)
    error = None

    if request.method == "POST":

        User.delete_user(user.userID)   
        return redirect('/admin')
    
    if request.method == "GET":     
        # display subtract points page
        return render_template('deleteuser.html', user=user)

@login_required
@app.route('/changepassword', methods=["GET", "POST"])
def changePassword():

    s = cfg.salt
    user = current_user
    error = None
    passwordRegex = re.compile('[@_!#$%^&*()<>?/\|}{~:]')

    if request.method == "POST":
        password = request.form['password']
        confirm = request.form['confirm']

        if password != confirm:
            error = 'Passwords do not match.'
            return render_template('changepassword.html', user=user, error=error)

        else:
            if (any(x.isupper() for x in password) 
            and any(x.islower() for x in password) 
            and any(x.isdigit() for x in password) 
            and len(password) >= 10 
            and re.search(passwordRegex, password) != None): 
                pw = (s + password).encode()

                pw_hash = hashlib.sha512(pw).hexdigest()
            else:
                error = 'Your password must be at least 10 characters long and contain an uppercase letter, a lowercase letter, and a symbol.'

            User.change_password(user.userID, pw_hash)

            flash("Password was changed.")
            return redirect(url_for('admin'))

    if request.method == "GET":     
        # display reset password page
        return render_template('changepassword.html', user=user, error=error)

@app.route('/about', methods=["GET", "POST"])
def about():

    if request.method == "GET":     

        return render_template('about.html')

@app.route('/forgotpassword', methods=['GET', 'POST'])
def forgotPassword():
    error = None
    if request.method == "POST":

        # get email address from form
        email = request.form['email']

        # get userID and User object
        try:
            userID = User.get_userID_from_email(email)
        except:
            error = 'That email does not match our records.'
            return render_template('forgotpassword.html', error=error)

        
        user = User.get_user(userID)

        # send email to user
        
        User.send_reset_email(user)

        return redirect(url_for('passwordchanged'))

    if request.method == "GET":

        # display login page
        return render_template('forgotpassword.html', error=error)

@app.route('/resetpasswordlink/<token>', methods=["GET", "POST"])
def resetPasswordLink(token):

    userID = verify_reset_token(token)
    error = None
    s = cfg.salt
    passwordRegex = re.compile('[@_!#$%^&*()<>?/\|}{~:]')

    user = User.get_user(userID)

    print(user.username)
    if request.method == "POST":

        if user == None:
            return render_template('invalidresetlink.html')

        password = request.form['password']
        confirm = request.form['confirm']

        if password != confirm:
        
            error = 'Passwords do not match.'
            return render_template('resetpasswordlink.html', user=user, error=error)

        elif (any(x.isupper() for x in password) 
            and any(x.islower() for x in password) 
            and any(x.isdigit() for x in password) 
            and len(password) >= 10 
            and re.search(passwordRegex, password) != None): 
            pw = (s + password).encode()
            pw_hash = hashlib.sha512(pw).hexdigest()
            User.change_password(user.userID, pw_hash)
            flash("Password was changed.")
            return redirect(url_for('login'))
        else:
            error = 'Your password must be at least 10 characters long and contain an uppercase letter, a lowercase letter, and a symbol.'
            return render_template('resetpasswordlink.html', user=user, error=error)

    if request.method == "GET":     

        # display reset password page
        return render_template('resetpasswordlink.html', user=user)

@app.route('/passwordchanged', methods=["GET", "POST"])
def passwordchanged():

    if request.method == "GET":     

        return render_template('passwordchanged.html')

if __name__ == "__main__":
    app.config['TRAP_BAD_REQUEST_ERRORS'] = True
    app.run(host="localhost", port=8080, debug=True)
