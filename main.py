from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from datetime import datetime, timedelta

app = Flask(__name__)

app.secret_key = 'S>&[8-$F?\:wtbX/'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'chorepoint'
app.config['MYSQL_UNIX_SOCKET'] = '/home/rio/mysql/mysqld.sock'
mysql = MySQL(app)

class Task(object):
    def __init__(self, taskID, taskName, points, approved, assignedUserID, createdByUserID, dateCreated, dateCompleted, frequency, dueDate, homeID, assignedUsername, active):
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
        return Task(taskID, task[0]['taskName'], task[0]['points'],  task[0]['approved'], task[0]['assignedUserID'], task[0]['createdByUserID'], task[0]['dateCreated'], task[0]['dateCompleted'], task[0]['frequency'], task[0]['dueDate'], task[0]['homeID'], assignedUsername, task[0]['active'])

    def get_home_tasks(homeID):

        # initialize home variable and mysql cursor
        h = (homeID,)
        cur = mysql.connection.cursor()

        # get taskIDs for homeID
        cur.execute("SELECT taskID FROM tasks WHERE homeID=%s", h)
        tasks = cur.fetchall()

        # return taskIDs
        return tasks
    
    def create_next_task(taskID, frequency):

        # initialize sql cursor
        cur = mysql.connection.cursor()

        # get last taskID and create new taskID
        cur.execute("SELECT taskID FROM tasks ORDER BY taskID DESC LIMIT 1")
        lastTaskID = cur.fetchall()[0]
        newTaskID = int((lastTaskID[0])) + 1
        approved = 0

        # set and format current date
        currentDate = datetime.now()
        formattedDate = str(currentDate.strftime('%Y-%m-%d'))
        dateString = "%Y-%m-%d"   

        # set and format due date based on frequency
        dueDate = currentDate + timedelta(int( ( ( frequency[0]) [0] ) ))
        formattedDueDate = str(dueDate.strftime('%Y-%m-%d'))

        # intialize sql cursor
        cur = mysql.connection.cursor()

        # add new task to database
        cur.execute("INSERT INTO tasks (taskID, taskName, points, approved, assignedUserID, createdByUserID, dateCreated, frequency, dueDate, homeID, active) SELECT %s, taskName, points, %s, assignedUserID, createdByUserID, STR_TO_DATE('%s','%s'), frequency, STR_TO_DATE('%s','%s'), homeID, 1 FROM tasks WHERE taskID=%s" % (newTaskID, approved, formattedDate, dateString, formattedDueDate, dateString, taskID))
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

class User(object):
    def __init__(self, userID, username, displayName, admin, passwordHash, approvalRequired, points):
        self.userID = userID
        self.username = username
        self.displayName = displayName
        self.admin = admin
        self.passwordHash = passwordHash
        self.approvalRequired = approvalRequired
        self.points = points

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
            return User(user[0]['userID'],user[0]['username'],user[0]['displayName'],user[0]['admin'],user[0]['passwordHash'],user[0]['approvalRequired'],user[0]['points'])

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

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == "POST":

        # get username and password from form
        username = request.form['username']
        password = request.form['password']

        # get userID and User object
        userID = User.get_userID_from_username(username)
        user = User.get_user(userID)

        error = None

        # check username and password 
        if user == None:
            error = 'Incorrect username.'
            print(error)
        else: 
            if user.passwordHash != password:    
                error = 'Incorrect password.'
            else:

                # initialize login session
                session['userID'] = user.userID

                # send user to correct page
                if user.admin == 1:
                    return redirect(url_for('admin'))
                else:
                    return redirect(url_for('user'))
    if request.method == "GET":                
        # display login page
        return render_template('login.html', error=error)

@app.route('/admin')

def admin():
    # get current logged in user
    userID = session['userID']    
    adminUser = User.get_user(userID)

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
def approveReward(rewardID):

    # initialize mysql cursor and rewardID variables
    cur = mysql.connection.cursor()
    r = (rewardID,)
    
    # approve reward
    cur.execute("UPDATE rewards SET approved=2 WHERE rewardID=%s", r)
    mysql.connection.commit()

    # create next reward
    Reward.create_next_reward(rewardID)

    return redirect(url_for('admin'))

@app.route('/admin/denyReward/<rewardID>', methods=['GET'])
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

    return redirect(url_for('admin'))

@app.route('/admin/deleteReward/<rewardID>', methods=['GET'])
def deleteReward(rewardID):

    # initialize mysql cursor and rewardID variables
    cur = mysql.connection.cursor()
    r = (rewardID,)
    
    # deactivate reward
    cur.execute("UPDATE rewards SET active=0 WHERE rewardID=%s", r)
    mysql.connection.commit()

    return redirect(url_for('admin'))


@app.route('/admin/approveTask/<taskID>', methods=['GET', 'POST'])   
def approveTask(taskID):

    # initialize mysql cursor and taskID variables
    cur = mysql.connection.cursor()
    t = taskID
    i = (taskID,)

    # get and format current date
    currentDate = datetime.now()
    formattedDate = str(currentDate.strftime('%Y-%m-%d'))
    dateString = "%Y-%m-%d"

    # approve task and update date completed
    cur.execute("UPDATE tasks SET approved=2, dateCompleted=STR_TO_DATE('%s', '%s') WHERE taskID=%s" % (formattedDate, dateString, t))
    mysql.connection.commit()

    # create new task based on frequency
    task = Task.get_task(taskID)
    Task.create_next_task(taskID, task.frequency)
    
    # add points to user
    User.add_points(task.assignedUserID, task.points)

    return redirect(url_for('admin'))

@app.route('/admin/denyTask/<taskID>', methods=['GET', 'POST'])
def denyTask(taskID):
    # initialize mysql cursor and taskID variables
    cur = mysql.connection.cursor()
    t = (taskID,)
    
    # deny task
    cur.execute("UPDATE tasks SET approved=0 WHERE taskID=%s", t)
    mysql.connection.commit()

    return redirect(url_for('admin'))

@app.route('/admin/deleteTask/<taskID>', methods=['GET', 'POST'])
def deleteTask(taskID):
    # initialize mysql cursor and taskID variables
    cur = mysql.connection.cursor()
    t = (taskID,)
    
    # deactivate task
    cur.execute("UPDATE tasks SET active=0 WHERE taskID=%s", t)
    mysql.connection.commit()

    return redirect(url_for('admin'))



@app.route('/user', methods=['GET', 'POST'])
def user():
    userID = session['userID']
    user = User.get_user(userID)

    currentDate = datetime.now()
    formattedDate = str(currentDate.strftime('%Y-%m-%d'))
    
    userTasks = []

    userTasksTuple = Task.get_user_tasks(userID)
    print(userTasksTuple)
    for a in range(len(userTasksTuple)):
        userTasks.append(int(((userTasksTuple[a])[0])))

    userPendingTasks = []
    userActiveTasks = []
    userCompletedTasks = []

    for userTask in userTasks:
        thisTask = Task.get_task(userTask)

        if thisTask.approved == 0 and str(thisTask.dueDate) == formattedDate and thisTask.active == 1:        
            userActiveTasks.append(thisTask)
        elif thisTask.approved == 1 and thisTask.active == 1:
            userPendingTasks.append(thisTask)
        elif thisTask.approved == 2 and str(thisTask.dueDate) == formattedDate and thisTask.active ==1:
            userCompletedTasks.append(thisTask)

    
    userRewards = []    
    userRewardsTuple = Reward.get_user_rewards(userID)
    for a in range(len(userRewardsTuple)):
        userRewards.append(int(((userRewardsTuple[a])[0])))

    userAvailableRewards = []
    userPendingRewards = []
    userRedeemedRewards = []

    for userReward in userRewards:
        thisReward = Reward.get_reward(userReward)
        if thisReward.approved == 0 and thisReward.active==1:
            userAvailableRewards.append(thisReward)
        elif thisReward.approved == 1 and thisReward.active==1:
            userPendingRewards.append(thisReward)
        elif thisReward.approved == 2 and thisReward.active==1: 
            userRedeemedRewards.append(thisReward)

    return render_template('user.html', username = user.username, points = user.points, userActiveTasks=userActiveTasks, userPendingTasks=userPendingTasks, userCompletedTasks=userCompletedTasks, userAvailableRewards=userAvailableRewards, userPendingRewards=userPendingRewards, userRedeemedRewards=userRedeemedRewards)

@app.route('/user/redeem/<rewardID>')
def redeemReward(rewardID):
    cur = mysql.connection.cursor()
    
  
    reward = Reward.get_reward(rewardID)
    print(reward.assignedUserID)
    userID = reward.assignedUserID
    print(userID)
    user = User.get_user(userID)
    newPoints = user.points - reward.points

    n = newPoints
    r = (rewardID, )
    u = userID
    cur.execute("UPDATE rewards SET approved=1 WHERE rewardID=%s;", r)
    mysql.connection.commit()

    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET points=%s WHERE userID=%s" % (n, u))
    
    mysql.connection.commit()

    return redirect(url_for('user'))

@app.route('/user/submitTask/<taskID>', methods=['GET', 'POST'])
def submitTask(taskID):
    cur = mysql.connection.cursor()
    t = (taskID,)
    cur.execute("UPDATE tasks SET approved=1 WHERE taskID=%s", t)
    mysql.connection.commit()
    return redirect(url_for('user'))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
