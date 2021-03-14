from flask import Flask, render_template, request, redirect, url_for, session
from flask_login import current_user, logout_user, LoginManager, login_user, login_required
from flask_mysqldb import MySQL
from datetime import datetime, timedelta
import hashlib
import oak as cfg

app = Flask(__name__)
app.config.from_envvar("CHOREPOINT_SETTINGS")

mysql = MySQL(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

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
        dueDate = currentDate + timedelta(int(thisTask.frequency))
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

class User(object):
    def __init__(self, userID, username, displayName, admin, passwordHash, approvalRequired, points, homeID, is_authenticated, is_active, is_anonymous):
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
            return User(user[0]['userID'],user[0]['username'],user[0]['displayName'],user[0]['admin'],user[0]['passwordHash'],user[0]['approvalRequired'],user[0]['points'],user[0]['homeID'],user[0]['is_authenticated'],user[0]['is_active'],user[0]['is_anonymous'])

    def get_userID_from_username(username):

        # initialize username variable and mysql cursor
        u = (username,)
        cur = mysql.connection.cursor()

        # get userID for username
        cur.execute("SELECT userID FROM users WHERE username=%s", u)
        userTuple = cur.fetchall()
        user = int(((userTuple[0])[0]))

        # return userID
        return user

    def get_home_users(homeID):

        # initialize homeID variable and mysql cursor
        h = (homeID,)
        cur = mysql.connection.cursor()

        # get userIDs for homeID
        cur.execute("SELECT userID FROM users WHERE homeID=%s", h)

        # return userIDs
        users = cur.fetchall()
        return users
    
    def add_points(userID, points):

        # initialize user variable and sql cursor
        u = str(userID)
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

    def get_id(self):
        print("get id")
        userID = self.userID
        # return unicode user ID
        return userID

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

        # get home for admin user
        cur.execute("SELECT * FROM homes WHERE adminUserID=%s", u)
        columns = [col[0] for col in cur.description]
        home = [dict(zip(columns, row)) for row in cur.fetchall()]

        # return home object
        self.homeID = home[0]['homeID'] 
        self.homeName = home[0]['homeName']
        self.adminUserID = adminUserID
        return self

@login_manager.user_loader
def load_user(userID):
    print("load_user")
    try:
        user = User.get_user(userID)
        print(user.username)
        return User.get_user(userID)
    except:
        return None

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/bootstrap.min.css")
def bootstrap_css():
    return render_template('bootstrap.min.css')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    s = cfg.salt

    if request.method == "POST":

        # get username and password from form
        username = request.form['username']
        password = request.form['password']

        pw = (s + password).encode()
        pw_hash = hashlib.sha512(pw).hexdigest()

        # get userID and User object
        userID = User.get_userID_from_username(username)
        user = User.get_user(userID)

        error = None

        # check username and password 
        if user == None:
            error = 'Incorrect username.'
            print(error)
        else:

            if user.passwordHash != pw_hash:    
                error = 'Incorrect password.'
                print(error)
            else:
                # initialize login session
                
                userIDTuple = (user.userID,)
                cur = mysql.connection.cursor()
                cur.execute("UPDATE users SET is_authenticated=1 WHERE userID=%s", userIDTuple )
                mysql.connection.commit()
                user = User.get_user(userID)
                print(user.is_authenticated)
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

@app.route('/admin')
@login_required
def admin():
    # get current logged in user
    # userID = session['userID']    
    adminUser = current_user

    # get current home
    home = Home.get_home(adminUser.userID)

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
    for f in range(len(homeUsersTuple)):
        homeUsers.append(int(((homeUsersTuple[f])[0])))
    
    # add users to output
    allUsers=[]
    for g in range(len(homeUsers)):
        thisUser = User.get_user(homeUsers[g])
        allUsers.append(thisUser)

    # display admin page with output
    return render_template('admin.html',displayName=adminUser.displayName,home=home.homeName,allTasks=allTasks,allRewards=allRewards,allUsers=allUsers,pendingTasks=pendingTasks,pendingRewards=pendingRewards)

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

@app.route('/admin/newreward', methods=['GET','POST'])
@login_required
def createReward():
    if request.method == "POST":

        # get current user
        user = current_user

        # get reward info from form and user object
        rewardName = request.form['rewardName']
        points = request.form['points']
        homeID = user.homeID

        # create new reward
        Reward.create_new_reward(rewardName, points, homeID)

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
        points = request.form['points']
        assignedUserID = request.form['assignedUserID']
        createdByUserID = user.userID
        
        homeID = user.homeID

        # create new task for future date
        Task.create_new_task(taskName, points, assignedUserID, createdByUserID, frequency, homeID, dueDate, permanent, oneOff)

        # return to admin page
        return redirect(url_for('admin'))

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
            if thisUser.userID != user.userID:
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
    
    # get tasks for current user
    userTasks = []
    userTasksTuple = Task.get_user_tasks(user.userID)
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
        elif thisTask.approved == 2  and thisTask.active ==1:
            userCompletedTasks.append(thisTask)
        elif thisTask.approved == 0  and thisTask.active == 1 and thisTask.dueDate > currentDate:
            userUpcomingTasks.append(thisTask)

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

    # display user page with resulting output
    return render_template('user.html', username = user.username, points = user.points, userActiveTasks=userActiveTasks, userPendingTasks=userPendingTasks, userCompletedTasks=userCompletedTasks, userAvailableRewards=userAvailableRewards, userPendingRewards=userPendingRewards, userRedeemedRewards=userRedeemedRewards, userUpcomingTasks=userUpcomingTasks)

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
        if thisTask.approved == 0  and thisTask.active == 1 and thisDate == currentDate:        
            selfActiveTasks.append(thisTask)
        elif thisTask.approved == 2  and thisTask.active == 1:
            selfCompletedTasks.append(thisTask)
        elif thisTask.approved == 0  and thisTask.active == 1 and thisDate != currentDate:
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
    return render_template('self.html', username = user.username, points = user.points, selfActiveTasks=selfActiveTasks, selfCompletedTasks=selfCompletedTasks, selfUpcomingTasks=selfUpcomingTasks, selfAvailableRewards=selfAvailableRewards, selfRedeemedRewards=selfRedeemedRewards)

@app.route('/self/newtask', methods=['GET','POST'])
@login_required
def createSelfTask():
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
        points = request.form['points']
        assignedUserID = user.userID
        createdByUserID = user.userID
        
        homeID = user.homeID

        # create new task for future date
        Task.create_new_task(taskName, points, assignedUserID, createdByUserID, frequency, homeID, dueDate, permanent, oneOff)

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

    # create new task based on frequency if not permanent
    task = Task.get_task(taskID)
    if task.permanent == 0:
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
        points = request.form['points']

        # create new reward
        Reward.create_new_reward(rewardName, points, user.userID)

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

if __name__ == "__main__":
    app.config['TRAP_BAD_REQUEST_ERRORS'] = True
    app.run(host="192.168.111.13", port=8080, debug=True)
