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
    def __init__(self, taskID, taskName, points, active, complete, approved, assignedUserID, createdByUserID, dateCreated, dateCompleted, frequency):
        self.taskID = taskID
        self.taskName = taskName
        self.points = points
        self.complete = complete
        self.approved = approved
        self.assignedUserID = assignedUserID
        self.createdByUserID = createdByUserID
        self.dateCreated = dateCreated
        self.dateCompleted = dateCompleted
        self.frequency = frequency
        self.homeID = homeID

    @classmethod

    def get_task(self, taskID):
        t = (taskID,)
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM tasks WHERE taskID=%s", t)
        columns = [col[0] for col in cur.description]
        task = [dict(zip(columns, row)) for row in cur.fetchall()]
        self.taskID = taskID 
        self.taskName = task[0]['taskName']
        self.points = task[0]['points']
        self.aproved = task[0]['approved']
        self.assignedUserID = task[0]['assignedUserID']
        self.createdByUserID = task[0]['createdByUserID']
        self.dateCreated = task[0]['dateCreated']
        self.dateCompleted = task[0]['dateCompleted']
        self.frequency = task[0]['frequency']
        self.dueDate = task[0]['dueDate']
        self.homeID = task[0]['homeID']
        return self

    def get_home_tasks(homeID):
        h = (homeID,)
        cur = mysql.connection.cursor()
        cur.execute("SELECT taskID FROM tasks WHERE homeID=%s", h)
        tasks = cur.fetchall()
        return tasks

class Reward(object):
    def __init__(self, rewardID, rewardName, points, redeemed, active, approved, redeemedBy, createdBy):
        self.rewardID = rewardID
        self.rewardName = rewardName
        self.points = points
        self.redeemed = redeemed
        self.active = active
        self.approved = approved
        self.redeemedBy = redeemedBy
        self.createdByUserID = createdByUserID
        self.createdBy = createdBy

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

    def get_user(self, username):
        u = (username,)
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s", u)
        columns = [col[0] for col in cur.description]
        user = [dict(zip(columns, row)) for row in cur.fetchall()]
        print(user)
        if user == []:
            return None
        else :    
            self.userID = user[0]['userID']
            self.username = username
            self.displayName = user[0]['displayName']
            self.admin = user[0]['admin']
            self.passwordHash = user[0]['passwordHash']
            self.approvalRequired = user[0]['approvalRequired']
            self.points = user[0]['points']
            return self

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

        user = User.get_user(username)
        # print(user.userID)
        error = None

        if user == None:
            error = 'Incorrect username.'
            print(error)
        else: 
            if user.passwordHash != password:    
                error = 'Incorrect password.'
            else:
                session['username'] = user.username
                print('Logged in user:')
                print(session['username'])
                if user.admin == 1:
                    return redirect(url_for('admin'))
                else:
                    return redirect(url_for('user'))
    return render_template('login.html', error=error)

@app.route('/admin')

def admin():
    username = session['username']
    adminUser = User.get_user(username)
    # print(adminUser.userID)
    home = Home.get_home(adminUser.userID)
    # print(home.homeID)
    homeTasks = []
    homeTasksTuple = Task.get_home_tasks(home.homeID)
    for x in range(len(homeTasksTuple)):
        homeTasks.append(int(((homeTasksTuple[x])[0])))
        print(homeTasks[x])
    
    allTasks=[]

    for y in range(len(homeTasks)):
        thisTask = Task.get_task(homeTasks[y]) 
        allTasks.append(copy.deepcopy(thisTask))
        print(allTasks[y].taskName)

    #print(allTasks[10].taskName)

    for z in range(len(allTasks)):
        print(z)
        print(allTasks[z].taskName)


    return render_template('admin.html',displayName=adminUser.displayName)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
