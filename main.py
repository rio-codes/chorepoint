from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
from flask_table import Table, Col, LinkCol, ButtonCol

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'chorepoint'
app.config['MYSQL_UNIX_SOCKET'] = '/home/rio/mysql/mysqld.sock'
mysql = MySQL(app)

class TaskTable(Table):
    taskName = Col('Task Name')
    points = Col('Points')
    assignedUserID = Col('Assigned User ID')
    frequency = Col('Frequency')

class RewardTable(Table):
    rewardID=Col('Reward ID')
    rewardName = Col('Reward Name')
    points = Col('Points')    

class PendingRewardTable(Table):
    rewardName = Col('Reward Name')
    points = Col('Points')
    approved = ButtonCol('Approve', 'approveReward', url_kwargs=dict(rewardID='rewardID'))

class PendingTaskTable(Table):
    taskName = Col('Task Name')
    points = Col('Points')
    assignedUserID = Col('Assigned User ID')
    frequency = Col('Frequency')
    approved = ButtonCol('Approve', 'approveTask', url_kwargs=dict(taskID='taskID'))

class Task(object):
    def __init__(self, taskID, taskName, points, active, complete, approved, assignedUserID, createdByUserID, dateCreated, dateCompleted, frequency):
        self.taskID = taskID
        self.taskName = taskName
        self.points = points
        self.active = active
        self.complete = complete
        self.approved = approved
        self.assignedUserID = assignedUserID
        self.createdByUserID = createdByUserID
        self.dateCreated = dateCreated
        self.dateCompleted = dateCompleted
        self.frequency = frequency

    @classmethod

    def get_tasks(cls):
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM tasks")
        columns = [col[0] for col in cur.description]
        tasks = [dict(zip(columns, row)) for row in cur.fetchall()]
        return tasks

    @classmethod

    def get_tasks_pending_approval(cls):
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM tasks WHERE approved=1")
        columns = [col[0] for col in cur.description]
        tasks = [dict(zip(columns, row)) for row in cur.fetchall()]
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

    @classmethod

    def get_rewards(cls):
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM rewards")
        columns = [col[0] for col in cur.description]
        rewards = [dict(zip(columns, row)) for row in cur.fetchall()]
        return rewards

    @classmethod

    def get_rewards_pending_approval(cls):
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM rewards WHERE approved=1")
        columns = [col[0] for col in cur.description]
        rewards = [dict(zip(columns, row)) for row in cur.fetchall()]
        return rewards

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        error = None
        cur = mysql.connection.cursor()
        u = (username,)
        print(u)
        cur.execute("SELECT * FROM users WHERE username=%s", u)
        fullUser = cur.fetchall()
        
        print(fullUser)

        if fullUser == ():
            error = 'Incorrect username.'
            print(error)
        else:
            user = tuple(fullUser[0]) 
            if user[4] != password:    
                error = 'Incorrect password.'
                print(user[1])
                print(error)
            else:
                if user[3] == 1:
                    return redirect(url_for('admin'))
                else:
                    return redirect(url_for('user'))
    return render_template('login.html')



@app.route('/admin')

def admin():
    tasks = Task.get_tasks()
    pendingTasks = Task.get_tasks_pending_approval()
    pendingRewards = Reward.get_rewards_pending_approval()
    #print(tasks)
    #print(pendingTasks)
    print(pendingRewards)
    taskTable = TaskTable(tasks)
    pendingTaskTable = PendingTaskTable(pendingTasks)
    pendingRewardTable = PendingRewardTable(pendingRewards)
    return render_template('admin.html', activeTaskTable=taskTable, pendingTaskTable=pendingTaskTable, pendingRewardTable=pendingRewardTable)
    # , pendingTaskTable, pendingRewardTable, activeTaskTable, activeRewardTable, userTable

@app.route('/admin/rewardApproval/<rewardID>', methods=['GET', 'POST'])   
def approveReward(rewardID):
    # if request.method == "POST":
    cur = mysql.connection.cursor()
    r = rewardID
    print(r)
    cur.execute("UPDATE rewards SET approved=2 WHERE rewardID=%s", r)
    mysql.connection.commit()
    return redirect(url_for('admin'))

@app.route('/admin/taskApproval/<taskID>', methods=['GET', 'POST'])   
def approveTask(taskID):
    # if request.method == "POST":
    cur = mysql.connection.cursor()
    t = taskID
    print(t)
    cur.execute("UPDATE tasks SET approved=2 WHERE taskID=%s", t)
    mysql.connection.commit()
    return redirect(url_for('admin'))

#@app.route('/user', methods=['GET', 'POST'])
#def user():
    #return render_template('user.html', currentPoints, activeTaskTable, pendingTaskTable, completedTaskTable, rewardTable)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)


