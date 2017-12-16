import unicodecsv
from datetime import datetime as dt
from collections import defaultdict
import numpy as np
import pprint
import matplotlib.pyplot as plt

pp = pprint.PrettyPrinter()


#getting required files
engagement_filename='/Users/qureshi/Documents/workspace/Udacity/practice1/daily_engagement.csv'
enrollment_filename='/Users/qureshi/Documents/workspace/Udacity/practice1/enrollments.csv'
submission_filename='/Users/qureshi/Documents/workspace/Udacity/practice1/project_submissions.csv'


#funtion to read files
def read_csv(a):
    with open (a, 'rb') as f:
        reader = unicodecsv.DictReader(f)
        a=list(reader)
        #print (a[0])
        return a

enrollments = read_csv(enrollment_filename)
engagements = read_csv(engagement_filename)
submissions = read_csv(submission_filename)


# correcting data types
def parse_date(date):
    if date == '':
        return None
    else:
        return dt.strptime(date, '%Y-%m-%d')

def parse_maybe_int(i):
    if i == '':
        return None
    else:
        return int(i)



# clean up for enrollments
for enrollment in enrollments:
    enrollment['join_date']= parse_date(enrollment['join_date'])
    enrollment['cancel_date']= parse_date(enrollment['cancel_date'])
    enrollment['days_to_cancel']= parse_maybe_int(enrollment['days_to_cancel'])
    enrollment['is_udacity']= enrollment['is_udacity']=='True'
    enrollment['is_canceled']=enrollment['is_canceled']=='True'

# clean up for engagements
for engagement in engagements:
    engagement['utc_date']=parse_date(engagement['utc_date'])
    engagement['num_courses_visited']=int(float(engagement['num_courses_visited']))
    engagement['total_minutes_visited']=float(engagement['total_minutes_visited'])
    engagement['lessons_completed']=int(float(engagement['lessons_completed']))
    engagement['projects_completed']=int(float(engagement['projects_completed']))

# clean up for submissions
for submission in submissions:
    submission['creation_date']=parse_date(submission['creation_date'])
    submission['completion_date']=parse_date(submission['completion_date'])



#function for finding total number of lines in file
def total_rows(a):
    return len(a)+1

enrollment_num_rows= total_rows(enrollments)
engagement_num_rows= total_rows(engagements)
submission_num_rows= total_rows(submissions)
print("total no. of rows in csv files,enrolled ={}, engaged ={}, submitted ={} ".format(enrollment_num_rows,engagement_num_rows,submission_num_rows))


#function for replacing undesired key names
def replacekey(d,old_key,new_key):
    for r in d:
        r[new_key] = r[old_key]
        del r[old_key]
    return d

engagements = replacekey(engagements,'acct','account_key')



#function for calculating unique accounts(from account_key)
def get_unique_students(data):
    unique_students = set()
    for data_set in data:
        unique_students.add(data_set['account_key'])
    return unique_students

unique_enrolled_students = get_unique_students(enrollments)
unique_engagement_students = get_unique_students(engagements)
unique_project_submitters = get_unique_students(submissions)

print("length of unique students, enrolled ={}, engaged ={}, submitted ={}".format(len(unique_enrolled_students), len(unique_engagement_students), len(unique_project_submitters)))



# Create a set of the account keys for all test accounts
udacity_test_accounts = set()
for enrollment in enrollments:
    #print (enrollment)
    if enrollment['is_udacity']:# never gets true?, why
        udacity_test_accounts.add(enrollment['account_key'])
print('no. of test accounts',len(udacity_test_accounts)) # mistake, ask zaid



# Given some data with an account_key field, removes any records corresponding to test accounts
def remove_test_accounts(data):
    non_udacity_data = []
    for data_point in data:
        if data_point['account_key'] not in udacity_test_accounts:
            non_udacity_data.append(data_point)
    return non_udacity_data


# Remove test accounts from all three tables
without_test_acc_enrollments = remove_test_accounts(enrollments)
without_test_acc_engagements = remove_test_accounts(engagements)
without_test_acc_submissions = remove_test_accounts(submissions)

print ('without_test_acc_enrollments =',len(without_test_acc_enrollments))
print ('without_test_acc_engagements =',len(without_test_acc_engagements))
print ('without_test_acc_submissions =',len(without_test_acc_submissions))


#calculating students who paid there fees,(refund was available only within a week of payment)
#So we can find this by students who have cancelled after 7 days or who are currently active
paid_students = {}
for enrollment in without_test_acc_enrollments:
    if (not enrollment['is_canceled'] or enrollment['days_to_cancel'] > 7):
        account_key = enrollment['account_key']
        join_date = enrollment['join_date']
        if (account_key not in paid_students or join_date > paid_students[account_key]):
            paid_students[account_key] = join_date
print('no. of paid students =', len(paid_students))


def within_one_week(join_date, engagement_date):
    time_delta = engagement_date - join_date
    return time_delta.days < 7 and time_delta.days >= 0

def remove_free_trial_cancels(data):
    new_data = []
    for data_point in data:
        if data_point['account_key'] in paid_students:
            new_data.append(data_point)
    return new_data

paid_enrollments = remove_free_trial_cancels(without_test_acc_enrollments)
paid_engagements = remove_free_trial_cancels(without_test_acc_engagements)
paid_submissions = remove_free_trial_cancels(without_test_acc_submissions)
#pp.pprint(paid_engagements)

print ("paid enrollments = {}".format(len(paid_enrollments)))
print ("paid engagements = {}".format(len(paid_engagements)))
print ("paid submissions = {}".format(len(paid_submissions)))



#added a field to get information about attendance per student
#will be summarised in the later completion_date
for v in paid_engagements:
    if v['num_courses_visited']>0:
        v['has_visited']=1
    else:
        v['has_visited']=0
#pp.pprint(paid_engagements[0])


#arranging record of students who paid fees within first week
paid_engagement_in_first_week = []
for engagement_record in paid_engagements:
    account_key = engagement_record['account_key']
    join_date = paid_students[account_key]
    engagement_record_date = engagement_record['utc_date']

    if within_one_week(join_date, engagement_record_date):
         paid_engagement_in_first_week.append(engagement_record)

print("paid engagements in first week = {}".format(len(paid_engagement_in_first_week)))
#print(paid_engagement_in_first_week)


# dictionary of engagement grouped by student.
# The keys are account keys, and the values are lists of engagement records.
engagement_by_account = defaultdict(list)
for engagement_record in paid_engagement_in_first_week:
    account_key = engagement_record['account_key']
    engagement_by_account[account_key].append(engagement_record)
#pp.pprint(engagement_by_account)


# fuction to get any data value from dictinary
def group_data(dict,value):
    total_data_by_account={}
    for account_key, engagement_for_student in dict.items():
        total_data = 0
        for engagement_record in engagement_for_student:
            total_data += engagement_record[value]
        total_data_by_account[account_key] = total_data
    return total_data_by_account



#convert to list data types
def create_list_from_byAccountDict(a):
    data = []
    for x in a.values():
        data.append(x)
    return data

#getting statistics for different type of students
def describe_data(list):
    print ('Mean:', np.mean(list))
    print ('Standard deviation:', np.std(list))
    print ('Minimum:', np.min(list))
    print ('Maximum:', np.max(list))



# a dictionary with the total minutes each student spent in the classroom during the first week.
# The keys are account keys, and the values are total minutes
# Summarize the data about minutes spent in the classroom

total_minutes_by_account = group_data(engagement_by_account,'total_minutes_visited')
total_minutes = create_list_from_byAccountDict(total_minutes_by_account)
describe_data(total_minutes)


#debugging problem
max_minutes = 0
student_with_max_minutes = None
for student_acc, minutes in total_minutes_by_account.items():
    if max_minutes < minutes:
        max_minutes = minutes
        student_with_max_minutes = student_acc
# for engagement in paid_engagement_in_first_week:
#     if engagement['account_key'] == student_with_max_minutes:
#         a =0#pp.pprint(engagement)


#total lessons completed by student
total_lessons_by_account = group_data(engagement_by_account,'lessons_completed')
total_lessons = create_list_from_byAccountDict(total_lessons_by_account)
describe_data(total_lessons)

# Summarize the data about classroom attendance by each student
total_visits_classroom = group_data(engagement_by_account,'has_visited')
total_visits = create_list_from_byAccountDict(total_visits_classroom)
describe_data(total_visits)



#calculating parameters of students who passed first projects
# lesson key of first project ['746169184' , '3176718735']
subway_passed = set()
req_lesson = ['746169184' , '3176718735']
for data in paid_submissions:
    lesson = data['lesson_key']
    if (lesson in req_lesson) \
    and ((data['assigned_rating'] == 'PASSED' or data['assigned_rating'] =='DISTINCTION')):
        subway_passed.add(data['account_key'])

print(len(subway_passed))
#print(subway_passed)



passing_engagement = []
non_passing_engagement = []
for engagement in paid_engagement_in_first_week:
    if engagement['account_key'] in subway_passed:
        passing_engagement.append(engagement_by_account[engagement['account_key']])
    else:
        a = data['account_key']
        non_passing_engagement.append(engagement_by_account[engagement['account_key']])

print(len(engagement_by_account))
print(len(passing_engagement),len(non_passing_engagement))


#differentiating the data with students passed and non passed
lesson_completed_passing_students = []
lesson_completed_non_passing_students = []

for key , value in total_lessons_by_account.items():
    if key in subway_passed:
        lesson_completed_passing_students.append(value)
    else:
        lesson_completed_non_passing_students.append(value)

#pp.pprint(passing_engagement)
describe_data(lesson_completed_passing_students)
describe_data(lesson_completed_non_passing_students)


#visuals of one parameter, you can do as many you want
plt.hist(lesson_completed_passing_students)
plt.hist(lesson_completed_non_passing_students)
plt.show()
