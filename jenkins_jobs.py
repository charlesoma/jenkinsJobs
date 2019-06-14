from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import jenkins


Base = declarative_base()


def connectToJenkins(url, username, password):
    server = jenkins.Jenkins(url,
                             username=username, password=password)
    return server


def initializeDb():
    engine = create_engine('sqlite:///cli.db', echo=False)
    session = sessionmaker(bind=engine)()
    Base.metadata.create_all(engine)
    return session


def addJob(session, myJobList):
    for k in myJobList:
        session.add(k)
    session.commit()


def getLastJobId(session, name):
    jobs = session.query(Jobs).filter_by(name=name).order_by(Jobs.jen_id.desc()).first()
    if (jobs != None):
        return jobs.jen_id
    else:
        return None


class Jobs(Base):
    __tablename__ = 'Jobs'

    id = Column(Integer, primary_key=True)
    jen_id = Column(Integer)
    name = Column(String)
    timeStamp = Column(DateTime)
    result = Column(String)
    building = Column(String)
    estimatedDuration = Column(String)


def createJobList(start, lastBuildNumber, jobName):
    myJobList = [] 
    for n in range(start + 1, lastBuildNumber + 1):
        current = server.get_build_info(jobName, n)
        current_as_jobs = Jobs()
        current_as_jobs.jen_id = current['id']
        current_as_jobs.building = current['building']
        current_as_jobs.estimatedDuration = current['estimatedDuration']
        current_as_jobs.name = jobName
        current_as_jobs.result = current['result']
        current_as_jobs.timeStamp = datetime.datetime.fromtimestamp(int(current['timestamp']) * 0.001)
        myJobList.append(current_as_jobs)
    return myJobList


url = 'http://localhost:8080'
username = input('Enter username: ') 
password = input('Enter password: ')
server = connectToJenkins(url, username, password)

authenticated = false
try:
    server.get_whoami()
    authenticated = true
except jenkins.JenkinsException as e:
    print
    'Authentication error'
    authenticated = false

if authenticated:
    session = initializeDb()

    jobs = server.get_all_jobs()
    for m in jobs:
        jobName = m['name']  
        lastJobId = getLastJobId(session, jobName) 
        lastBuildNumber = server.get_job_info(jobName)['lastBuild']['number'] 

        if lastJobId == None:
            start = 0
        else:
            start = lastJobId

        myJobList = createJobList(start, lastBuildNumber, jobName)
        addJob(session, myJobList)