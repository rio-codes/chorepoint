from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from flask_table import Table, Col, LinkCol, ButtonCol
from datetime import datetime, timedelta
import copy

app = Flask(__name__)

app.secret_key = 'S>&[8-$F?\:wtbX/'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'chorepoint'
app.config['MYSQL_UNIX_SOCKET'] = '/home/rio/mysql/mysqld.sock'
mysql = MySQL(app)

class Task(object):
    def __init__(self, taskID, taskName, points, approved, assignedUserID, createdByUserID, dateCreated, dateCompleted, frequency, dueDate, homeID, assignedUsername):
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

    def get_task(taskID):
        t = (taskID,)
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM tasks WHERE taskID=%s", t)
        columns = [col[0] for col in cur.description]
        task = [dict(zip(columns, row)) for row in cur.fetchall()]
        assignedUser = User.get_user(task[0]['assignedUserID'])
        assignedUsername = assignedUser.username
        return Task(taskID, task[0]['taskName'], task[0]['points'],  task[0]['approved'], task[0]['assignedUserID'], task[0]['createdByUserID'], task[0]['dateCreated'], task[0]['dateCompleted'], task[0]['frequency'], task[0]['dueDate'], task[0]['homeID'], assignedUsername)

    def get_home_tasks(homeID):
        h = (homeID,)
        cur = mysql.connection.cursor()
        cur.execute("SELECT taskID FROM tasks WHERE homeID=%s", h)
        tasks = cur.fetchall()
        return tasks

class Reward(object):
    def __init__(self, rewardID, rewardName, points, approved, assignedUserID, homeID):
        self.rewardID = rewardID
        self.rewardName = rewardName
        self.points = points
        self.approved = approved
        self.assignedUserID = assignedUserID
        self.homeID = homeID

    def get_reward(rewardID):
        r = (rewardID,)
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM rewards WHERE rewardID=%s", r)
        columns = [col[0] for col in cur.description]
        reward = [dict(zip(columns, row)) for row in cur.fetchall()]
        return Reward(rewardID, reward[0]['rewardName'], reward[0]['points'], reward[0]['approved'], reward[0]['assignedUserID'], reward[0]['homeID'])
    
    def get_home_rewards(homeID):
        h = (homeID,)
        cur = mysql.connection.cursor()
        cur.execute("SELECT rewardID FROM rewards WHERE homeID=%s", h)
        rewards = cur.fetchall()
        return rewards

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
        u = (userID,)
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE userID=%s", u)
        columns = [col[0] for col in cur.description]
        user = [dict(zip(columns, row)) for row in cur.fetchall()]
        if user == []:
            return None
        else :
            return User(user[0]['userID'],username,user[0]['displayName'],user[0]['admin'],user[0]['passwordHash'],user[0]['approvalRequired'],user[0]['points'])

    def get_userID_from_username(username):
        u = (username,)
        cur = mysql.connection.cursor()
        cur.execute("SELECT userID FROM users WHERE username=%s", u)
        userTuple = cur.fetchall()
        user = int(((userTuple[0])[0]))
        return user
        
    def get_home_users(homeID):
        h = (homeID,)
        cur = mysql.connection.cursor()
        cur.execute("SELECT username FROM users WHERE homeID=%s", h)
        users = cur.fetchall()
        return users

class Home(object):
    def __init__(self, homeID, homeName, adminUserID):
        self.homeID = homeID
        self.homeName = homeName
        self.adminUserID = adminUserID

    @classmethod

    def get_home(self, adminUserID):    
        u = (adminUserID,)
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM homes WHERE adminUserID=%s", u)
        columns = [col[0] for col in cur.description]
        home = [dict(zip(columns, row)) for row in cur.fetchall()]
        self.homeID = home[0]['homeID'] 
        self.homeName = home[0]['homeName']
        self.adminUserID = adminUserID
        return self

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        userID = User.get_userID_from_username(username)
        user = User.get_user(userID)

        error = None

        if user == None:
            error = 'Incorrect username.'
            print(error)
        else: 
            if user.passwordHash != password:    
                error = 'Incorrect password.'
            else:
                session['userID'] = user.userID
                print('Logged in user:')
                print(user.username)
                if user.admin == 1:
                    return redirect(url_for('admin'))
                else:
                    return redirect(url_for('user'))
    return render_template('login.html', error=error)

@app.route('/admin')

def admin():
    # get current logged in user
    username = session['username']
    adminUser = User.get_user(username)

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
        if thisTask.dateCompleted == None:
            allTasks.append(thisTask)
        elif thisTask.approved == 1:
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
        if thisReward.approved == 0:
            allRewards.append(thisReward)
        elif thisReward.approved == 1:
            pendingRewards.append(thisReward)

    # get users for current home
    homeUsers=[]
    homeUsersTuple = User.get_home_users(home.homeID)
    
    for f in range(len(homeUsersTuple)):
        homeUsers.append(str(((homeUsersTuple[f])[0])))
    
    # add users to output
    allUsers=[]
    for g in range(len(homeUsers)):
        thisUser = User.get_user(homeUsers[g])
        allUsers.append(thisUser)

    # display admin page with output
    return render_template('admin.html',displayName=adminUser.displayName,home=home.homeName,allTasks=allTasks,allRewards=allRewards,allUsers=allUsers,pendingTasks=pendingTasks,pendingRewards=pendingRewards)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
