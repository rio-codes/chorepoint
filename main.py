from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from flask_table import Table, Col, LinkCol, ButtonCol
from datetime import datetime, timedelta

app = Flask(__name__)

app.secret_key = 'S>&[8-$F?\:wtbX/'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'chorepoint'
app.config['MYSQL_UNIX_SOCKET'] = '/home/rio/mysql/mysqld.sock'
mysql = MySQL(app)

class frequencyCol(Col):
    def td_format(self, content):
        if content == '1':
            return 'every day'
        else:
            return 'every ' + content + ' days'

class usernameCol(Col):
    def td_format(self, content):
        username = User.get_username_from_userID(content)
        return username


class TaskTable(Table):
    taskName = Col('Task Name')
    points = Col('Points')
    assignedUserID = usernameCol('User')
    frequency = frequencyCol('Frequency')

class RewardTable(Table):
    rewardName = Col('Reward Name')
    points = Col('Points')    

class UserTable(Table):
    username = Col('Username')
    points = Col('Points') 
    admin = Col('Admin?')
    approvalRequired = Col('Approval Required?')

class PendingRewardTable(Table):
    rewardName = Col('Reward Name')
    points = Col('Points')
    approved = ButtonCol('Approve', 'approveReward', url_kwargs=dict(rewardID='rewardID'))

class PendingTaskTable(Table):
    taskName = Col('Task Name')
    points = Col('Points')
    assignedUserID = usernameCol('User')
    frequency = frequencyCol('Frequency')
    approved = ButtonCol('Approve', 'approveTask', url_kwargs=dict(taskID='taskID'))

class UserTaskTable(Table):
    taskName = Col('Task Name')
    points = Col('Points')
    submit = ButtonCol('Submit', 'submitTask', url_kwargs=dict(taskID='taskID'))

class UserPendingTaskTable(Table):
    taskName = Col('Task Name')
    points = Col('Points')

class UserCompletedTaskTable(Table):
    taskName = Col('Task Name')
    points = Col('Points')

class UserAvailableRewardsTable(Table):
    rewardName = Col('Reward Name')
    points = Col('Points')
    redeem = ButtonCol('Redeem', 'redeem', url_kwargs=dict(rewardID='rewardID'))

class UserPendingRewardsTable(Table):
    rewardName = Col('Reward Name')
    points = Col('Points')

class UserRedeemedRewardsTable(Table):
    rewardName = Col('Reward Name')
    points = Col('Points')

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
    
    def create_next_task(taskID, frequency):
        cur = mysql.connection.cursor()
        cur.execute("SELECT taskID FROM tasks ORDER BY taskID DESC LIMIT 1")
        lastTaskID = cur.fetchall()[0]
        newTaskID = int((lastTaskID[0])) + 1
        approved = 0

        currentDate = datetime.now()
        formattedDate = str(currentDate.strftime('%Y-%m-%d'))
        dateString = "%Y-%m-%d"   

        dueDate = currentDate + timedelta(int( ( ( frequency[0]) [0] ) ))
        formattedDueDate = str(dueDate.strftime('%Y-%m-%d'))

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO tasks (taskID, taskName, points, approved, assignedUserID, createdByUserID, dateCreated, frequency, dueDate) SELECT %s, taskName, points, %s, assignedUserID, createdByUserID, STR_TO_DATE('%s','%s'), frequency, STR_TO_DATE('%s','%s') FROM tasks WHERE taskID=%s" % (newTaskID, approved, formattedDate, dateString, formattedDueDate, dateString, taskID))
        mysql.connection.commit()


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
    
    def create_next_reward(rewardID):
        cur = mysql.connection.cursor()
        cur.execute("SELECT rewardID FROM rewards ORDER BY rewardID DESC LIMIT 1")
        lastRewardID = cur.fetchall()[0]
        newRewardID = int((lastRewardID[0])) + 1
        r = rewardID
        print(r)
        n = newRewardID
        print(n)
        a = 0
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO rewards (rewardID, rewardName, points, approved, assignedUserID) SELECT %s, rewardName, points, %s, assignedUserID FROM rewards WHERE rewardID=%s" % (n, a, r))
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

    def get_users(cls):
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users")
        columns = [col[0] for col in cur.description]
        users = [dict(zip(columns, row)) for row in cur.fetchall()]
        return users
    
    def get_current_user(username):
        u = (username,)
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s", u)
        columns = [col[0] for col in cur.description]
        user = [dict(zip(columns, row)) for row in cur.fetchall()]
        return user
    
    def get_points(username):
        u = (username,)
        cur = mysql.connection.cursor()
        cur.execute("SELECT points FROM users WHERE username=%s", u)
        points = cur.fetchall()[0]
        return points[0]

    def get_userID_from_username(username):
        u = (username,)
        cur = mysql.connection.cursor()
        cur.execute("SELECT userID FROM users WHERE username=%s", u)
        userID = cur.fetchall()[0]
        return userID[0]
    
    def get_username_from_userID(userID):
        u = (userID,)
        cur = mysql.connection.cursor()
        cur.execute("SELECT username FROM users WHERE userID=%s", u)
        username = cur.fetchall()[0]
        return username[0]

    def get_user_current_tasks(userID):
        u = (userID,)
        cur = mysql.connection.cursor()
        currentDate = datetime.now()
        formattedDate = str(currentDate.strftime('%Y-%m-%d'))
        dateString = "%Y-%m-%d"
        cur.execute("SELECT * FROM tasks WHERE assignedUserID='%s' AND approved=0 AND dueDate=STR_TO_DATE('%s','%s')" % (u, formattedDate, dateString))
        columns = [col[0] for col in cur.description]
        tasks = [dict(zip(columns, row)) for row in cur.fetchall()]
        return tasks

    def get_user_pending_tasks(userID):
        u = (userID,)
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM tasks WHERE (assignedUserID=%s AND approved=1)", u)
        columns = [col[0] for col in cur.description]
        tasks = [dict(zip(columns, row)) for row in cur.fetchall()]
        return tasks

    def get_user_completed_tasks(userID):
        u = userID
        cur = mysql.connection.cursor()
        currentDate = datetime.now()
        formattedDate = str(currentDate.strftime('%Y-%m-%d'))
        dateString = "%Y-%m-%d"
        cur.execute("SELECT * FROM tasks WHERE assignedUserID='%s' AND approved=2 AND dateCompleted=STR_TO_DATE('%s', '%s')" % (u, formattedDate, dateString))
        columns = [col[0] for col in cur.description]
        tasks = [dict(zip(columns, row)) for row in cur.fetchall()]
        return tasks
    
    def get_user_rewards(userID):
        u = (userID,)
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM rewards WHERE (assignedUserID=%s AND approved=0)", u)
        columns = [col[0] for col in cur.description]
        rewards = [dict(zip(columns, row)) for row in cur.fetchall()]
        return rewards

    def get_user_pending_rewards(userID):
        u = (userID,)
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM rewards WHERE (assignedUserID=%s AND approved=1)", u)
        columns = [col[0] for col in cur.description]
        rewards = [dict(zip(columns, row)) for row in cur.fetchall()]
        return rewards
    
    def get_user_redeemed_rewards(userID):
        u = (userID,)
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM rewards WHERE (assignedUserID=%s AND approved=2)", u)
        columns = [col[0] for col in cur.description]
        rewards = [dict(zip(columns, row)) for row in cur.fetchall()]
        return rewards
    
    def subtract_points(userID, points):

        print(points)
        u = str(userID)
        cur = mysql.connection.cursor()
        cur.execute("SELECT points FROM users WHERE userID=%s", u)
        currentPoints = (cur.fetchall()[0])[0]
        print(currentPoints)
        newPoints = currentPoints - int(points)

        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET points=%s WHERE userID=%s" % (newPoints, userID))
        mysql.connection.commit()
    
    def add_points(userID, points):

        print(points)
        u = str(userID)

        cur = mysql.connection.cursor()
        cur.execute("SELECT points FROM users WHERE userID=%s", u)
        currentPoints = (cur.fetchall()[0])[0]
        newPoints = currentPoints + int(points)

        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET points=%s WHERE userID=%s" % (newPoints, userID))
        mysql.connection.commit()

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
                session['username'] = user[1]
                print('Logged in user:')
                print(session['username'])
                if user[3] == 1:
                    return redirect(url_for('admin'))
                else:
                    return redirect(url_for('user'))
    return render_template('login.html')



@app.route('/admin')

def admin():
    username = session['username']

    tasks = Task.get_tasks()
    rewards = Reward.get_rewards()
    users = User.get_users()

    pendingTasks = Task.get_tasks_pending_approval()
    pendingRewards = Reward.get_rewards_pending_approval()

    taskTable = TaskTable(tasks)
    rewardTable = RewardTable(rewards)
    userTable = UserTable(users)

    pendingTaskTable = PendingTaskTable(pendingTasks)
    pendingRewardTable = PendingRewardTable(pendingRewards)

    return render_template('admin.html', activeTaskTable=taskTable, pendingTaskTable=pendingTaskTable, pendingRewardTable=pendingRewardTable, activeRewardTable=rewardTable, userTable=userTable, username=username)

@app.route('/admin/rewardApproval/<rewardID>', methods=['GET', 'POST'])   
def approveReward(rewardID):
    cur = mysql.connection.cursor()
    r = rewardID
    print(r)
    cur.execute("UPDATE rewards SET approved=2 WHERE rewardID=%s", r)
    mysql.connection.commit()

    cur = mysql.connection.cursor()
    cur.execute("SELECT assignedUserID, points FROM rewards WHERE rewardID=%s", r)
    userAndPoints = cur.fetchall()[0]
    assignedUserID = userAndPoints[0]
    points = userAndPoints[1]

    User.subtract_points(assignedUserID, points)

    return redirect(url_for('admin'))

@app.route('/admin/taskApproval/<taskID>', methods=['GET', 'POST'])   
def approveTask(taskID):
    cur = mysql.connection.cursor()
    t = taskID
    i = (taskID,)
    print(t)
    currentDate = datetime.now()
    print(currentDate)
    formattedDate = str(currentDate.strftime('%Y-%m-%d'))
    print(formattedDate)
    dateString = "%Y-%m-%d"
    print(taskID)
    cur.execute("UPDATE tasks SET approved=2, dateCompleted=STR_TO_DATE('%s', '%s') WHERE taskID=%s" % (formattedDate, dateString, t))
    mysql.connection.commit()

    cur = mysql.connection.cursor()
    cur.execute("SELECT frequency FROM tasks WHERE taskID=%s", i)
    
    frequency = cur.fetchall()[0]
    Task.create_next_task(taskID, frequency)
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT assignedUserID, points FROM tasks WHERE taskID=%s", i)
    userAndPoints = cur.fetchall()[0]
    userID = userAndPoints[0]
    points = userAndPoints[1]
    User.add_points(userID, points)

    return redirect(url_for('admin'))

@app.route('/user/submitTask/<taskID>', methods=['GET', 'POST'])
def submitTask(taskID):
    cur = mysql.connection.cursor()
    t = taskID
    print(t)
    cur.execute("UPDATE tasks SET approved=1 WHERE taskID=%s", t)
    mysql.connection.commit()
    return redirect(url_for('user'))

@app.route('/user/redeem/<rewardID>', methods=['GET', 'POST'])
def redeem(rewardID):
    r = rewardID
    print(r)
    cur = mysql.connection.cursor()
    cur.execute("SELECT assignedUserID FROM rewards WHERE rewardID=%s", [r])
    user = str((cur.fetchall()[0])[0])

    cur = mysql.connection.cursor()
    cur.execute("SELECT points FROM users WHERE userID=%s", user)
    userPoints = int((cur.fetchall()[0])[0])
    print(userPoints)

    cur = mysql.connection.cursor()
    cur.execute("SELECT points FROM rewards WHERE rewardID=%s", [r])
    rewardPoints = int((cur.fetchall()[0])[0])
    print(rewardPoints)

    if userPoints < rewardPoints:
        flash("You don't have enough points!")
        return redirect(url_for('notenough'))
    else:
        cur = mysql.connection.cursor()
        cur.execute("UPDATE rewards SET approved=1 WHERE rewardID=%s", r)
        mysql.connection.commit()
        Reward.create_next_reward(rewardID)
        return redirect(url_for('user'))

@app.route('/notenough', methods=['GET', 'POST'])
def notenough():
    return render_template('notenough.html')

@app.route('/user', methods=['GET', 'POST'])
def user():
    username = session['username']
    fullUser = User.get_current_user(username)
    points = User.get_points(username)
    userID = User.get_userID_from_username(username)

    userTasks = User.get_user_current_tasks(userID)
    userPendingTasks = User.get_user_pending_tasks(userID)
    userCompletedTasks = User.get_user_completed_tasks(userID)
    userAvailableRewards = User.get_user_rewards(userID)
    userPendingRewards = User.get_user_pending_rewards(userID)
    userRedeemedRewards = User.get_user_redeemed_rewards(userID)

    userTaskTable = UserTaskTable(userTasks)
    userPendingTaskTable = UserPendingTaskTable(userPendingTasks)
    userCompletedTaskTable = UserCompletedTaskTable(userCompletedTasks)
    userAvailableRewardsTable = UserAvailableRewardsTable(userAvailableRewards)
    userPendingRewardsTable = UserPendingRewardsTable(userPendingRewards)
    userRedeemedRewardsTable = UserRedeemedRewardsTable(userRedeemedRewards)

    return render_template('user.html', username=username, points=points, userTaskTable=userTaskTable, userPendingTaskTable=userPendingTaskTable, userCompletedTaskTable=userCompletedTaskTable, userAvailableRewardsTable=userAvailableRewardsTable, userPendingRewardsTable=userPendingRewardsTable, userRedeemedRewardsTable=userRedeemedRewardsTable)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)


