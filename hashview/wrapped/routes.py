from flask import Blueprint, render_template
from flask_login import login_required, current_user
from hashview.models import Tasks, Users, Hashes
from hashview.models import db
from sqlalchemy import func, or_
import datetime

wrapped = Blueprint('wrapped', __name__)

@wrapped.route("/wrapped", methods=['GET'])
@login_required
def wrapped_list():

    # Get previous year (will need to update this once we're ready to go live)
    year = datetime.datetime.now().year
    date_start = str(year) + '-01-01'
    date_end = str(year) + '-12-31'

    # Longest Password all
    #select h.id,h.recovered_at,CAST(unhex(h.plaintext) AS CHAR(100)),u.email_address from hashes as h join users as u on h.recovered_by = u.id where h.recovered_at > '2025-01-01' and h.recovered_at < '2026-01-01' ORDER BY LENGTH(h.plaintext) DESC limit 10;
    longest_password_all_table_raw = db.session.query(Hashes.plaintext, Hashes.recovered_at, Users.email_address).join(Users, Hashes.recovered_by==Users.id) \
        .filter(Hashes.cracked == '1') \
        .filter(Hashes.recovered_at > date_start) \
        .filter(Hashes.recovered_at < date_end) \
        .order_by(func.length(Hashes.plaintext).desc(), Hashes.recovered_at.asc()) \
        .limit(10) \
        .all()

    longest_password_all_table = []
    for entry in longest_password_all_table_raw:
        dict_entry = {}
        dict_entry['length'] = len(bytes.fromhex(entry.plaintext).decode('latin-1'))
        dict_entry['recovered_at'] = entry.recovered_at
        dict_entry['plaintext'] = bytes.fromhex(entry.plaintext).decode('latin-1')
        dict_entry['email_address'] = entry.email_address
        longest_password_all_table.append(dict_entry)

    # Longest Password Personal
    longest_password_personal_raw = db.session.query(Hashes.plaintext) \
        .filter(Hashes.cracked == '1') \
        .filter(Hashes.recovered_at > date_start) \
        .filter(Hashes.recovered_at < date_end) \
        .order_by(func.length(Hashes.plaintext).desc(), Hashes.recovered_at.asc()) \
        .filter(Hashes.recovered_by == current_user.id) \
        .first()

    longest_password_personal = bytes.fromhex(longest_password_personal_raw.plaintext).decode('latin-1')

    # Find what position the person is for password length
    longest_password_all_raw = db.session.query(Hashes.plaintext, Hashes.recovered_by) \
        .filter(Hashes.cracked == '1') \
        .filter(Hashes.recovered_at > date_start) \
        .filter(Hashes.recovered_at < date_end) \
        .order_by(func.length(Hashes.plaintext).desc()) \
        .all()   
    
    #longest_password_personal_rank = 0
    longest_password_all_cnt = len(longest_password_all_raw) -1
    longest_password_personal_rank = 1
    for entry in longest_password_all_raw:
        if entry.recovered_by == current_user.id:
            break
        elif entry.recovered_by != None:
            longest_password_personal_rank += 1

    # Most Passwords Recovered by user:
    # select count(h.id),u.email_address from hashes as h join users as u on h.recovered_by = u.id where h.recovered_by is not NULL and h.recovered_at > '2025-01-01' and h.cracked = '1' group by h.recovered_by ORDER BY COUNT(h.id) DESC LIMIT 10;
    most_passwords_recovered_all_raw = db.session.query(Hashes.recovered_by, Users.email_address, func.count(Hashes.id).label("row_count")).join(Users, Hashes.recovered_by == Users.id) \
        .filter(Hashes.cracked == '1') \
        .filter(Hashes.recovered_at > date_start) \
        .filter(Hashes.recovered_at < date_end) \
        .group_by(Hashes.recovered_by) \
        .order_by(func.count(Hashes.id).desc()) \
        .limit(10) \
        .all()

    most_passwords_recovered_all_table = []
    for entry in most_passwords_recovered_all_raw:
        dict_entry = {}
        dict_entry['count'] = entry.row_count
        dict_entry['email_address'] = entry.email_address
        most_passwords_recovered_all_table.append(dict_entry)

    # Total Passwords by you
    total_passwords_recovered = db.session.query(Hashes.recovered_by) \
        .filter(Hashes.cracked == '1') \
        .filter(Hashes.recovered_at > date_start) \
        .filter(Hashes.recovered_at < date_end) \
        .group_by(Hashes.recovered_by) \
        .order_by(func.count(Hashes.id).desc()) \
        .all()

    total_passwords_recovered_personal_pct = 0
    personal_group_by_pos = len(total_passwords_recovered) -1
    for entry in total_passwords_recovered:
        if entry.recovered_by == current_user.id:
            total_passwords_recovered_personal_pct = round(personal_group_by_pos / (len(total_passwords_recovered)-1), 2) * 100
            break
        else:
            personal_group_by_pos -= 1

    # Total password personal cnt
    total_passwords_recovered_personal_cnt = db.session.query(Hashes.id) \
        .filter(Hashes.cracked == '1') \
        .filter(Hashes.recovered_at > date_start) \
        .filter(Hashes.recovered_at < date_end) \
        .filter(Hashes.recovered_by == current_user.id) \
        .count() 

    #total_passwords_recovered_personal = total_passwords_recovered_personal_raw
    #total_passwords_recovered_personal_pct = total_passwords_recovered_personal / total_passwords_recovered_all_cnt

    # Total NTLM recovered
    total_ntlm_recovered_all_raw = db.session.query(Hashes.recovered_by, Users.email_address, func.count(Hashes.id).label("row_count")).join(Users, Hashes.recovered_by == Users.id) \
        .filter(Hashes.cracked == '1') \
        .filter(Hashes.recovered_at > date_start) \
        .filter(Hashes.recovered_at < date_end) \
        .filter(Hashes.hash_type == 1000) \
        .group_by(Hashes.recovered_by) \
        .order_by(func.count(Hashes.id).desc()) \
        .limit(10) \
        .all()

    total_ntlm_recovered_all_table = []
    for entry in total_ntlm_recovered_all_raw:
        dict_entry = {}
        dict_entry['count'] = entry.row_count
        dict_entry['email_address'] = entry.email_address
        total_ntlm_recovered_all_table.append(dict_entry)
    
    # Total NTLM recovered
    total_ntlm_recovered_all = db.session.query(Hashes.recovered_by) \
        .filter(Hashes.cracked == '1') \
        .filter(Hashes.recovered_at > date_start) \
        .filter(Hashes.recovered_at < date_end) \
        .filter(Hashes.hash_type == 1000) \
        .group_by(Hashes.recovered_by) \
        .order_by(func.count(Hashes.id).desc()) \
        .all()

    total_ntlm_recovered_personal_pct = 0
    personal_group_by_pos = len(total_ntlm_recovered_all) -1
    for entry in total_ntlm_recovered_all:
        if entry.recovered_by == current_user.id:
            total_ntlm_recovered_personal_pct = round(personal_group_by_pos / (len(total_ntlm_recovered_all)-1), 2) * 100
            break
        else:
            personal_group_by_pos -= 1

    # Personal NTLM recovered
    total_ntlm_recovered_personal_cnt = db.session.query(Hashes.id) \
        .filter(Hashes.cracked == '1') \
        .filter(Hashes.recovered_at > date_start) \
        .filter(Hashes.recovered_at < date_end) \
        .filter(Hashes.recovered_by == current_user.id) \
        .filter(Hashes.hash_type == 1000) \
        .count()

    # Total NetNTLMv2 recovered
    total_ntlmv2_recovered_all_raw = db.session.query(Hashes.recovered_by, Users.email_address, func.count(Hashes.id).label("row_count")).join(Users, Hashes.recovered_by == Users.id) \
        .filter(Hashes.cracked == '1') \
        .filter(Hashes.recovered_at > date_start) \
        .filter(Hashes.recovered_at < date_end) \
        .filter(or_(Hashes.hash_type == 5500, Hashes.hash_type == 5600, Hashes.hash_type == 27000, Hashes.hash_type == 27100)) \
        .group_by(Hashes.recovered_by) \
        .order_by(func.count(Hashes.id).desc()) \
        .limit(10) \
        .all()

    total_ntlmv2_recovered_all_table = []
    for entry in total_ntlmv2_recovered_all_raw:
        dict_entry = {}
        dict_entry['count'] = entry.row_count
        dict_entry['email_address'] = entry.email_address
        total_ntlmv2_recovered_all_table.append(dict_entry)
    
    # Total NTLMv2 recovered cnt
    total_ntlmv2_recovered_all = db.session.query(Hashes.recovered_by) \
        .filter(Hashes.cracked == '1') \
        .filter(Hashes.recovered_at > date_start) \
        .filter(Hashes.recovered_at < date_end) \
        .filter(or_(Hashes.hash_type == 5500, Hashes.hash_type == 5600, Hashes.hash_type == 27000, Hashes.hash_type == 27100)) \
        .group_by(Hashes.recovered_by) \
        .order_by(func.count(Hashes.id).desc()) \
        .all()
    
    total_ntlmv2_recovered_personal_pct = 0
    personal_group_by_pos = len(total_ntlmv2_recovered_all) -1
    for entry in total_ntlmv2_recovered_all:
        if entry.recovered_by == current_user.id:
            total_ntlmv2_recovered_personal_pct = round(personal_group_by_pos / (len(total_ntlmv2_recovered_all)-1), 2) * 100
        else:
            personal_group_by_pos -= 1


    # Personal NTLMv2 Recovered
    total_ntlmv2_recovered_personal_cnt = db.session.query(Hashes.id) \
        .filter(Hashes.cracked == '1') \
        .filter(Hashes.recovered_at > date_start) \
        .filter(Hashes.recovered_at < date_end) \
        .filter(Hashes.recovered_by == current_user.id) \
        .filter(or_(Hashes.hash_type == 5500, Hashes.hash_type == 5600, Hashes.hash_type == 27000, Hashes.hash_type == 27100)) \
        .count()

    # Total Kerberos Recovered
    total_kerberos_recovered_all_raw = db.session.query(Hashes.recovered_by, Users.email_address, func.count(Hashes.id).label("row_count")).join(Users, Hashes.recovered_by == Users.id) \
        .filter(Hashes.cracked == '1') \
        .filter(Hashes.recovered_at > date_start) \
        .filter(Hashes.recovered_at < date_end) \
        .filter(Hashes.hash_type == 13100) \
        .group_by(Hashes.recovered_by) \
        .order_by(func.count(Hashes.id).desc()) \
        .limit(10) \
        .all()

    total_kerberos_recovered_all_table = []
    for entry in total_kerberos_recovered_all_raw:
        dict_entry = {}
        dict_entry['count'] = entry.row_count
        dict_entry['email_address'] = entry.email_address
        total_kerberos_recovered_all_table.append(dict_entry)
    
    # Total kerberos recovered cnt
    total_kerberos_recovered_all = db.session.query(Hashes.recovered_by, func.count(Hashes.id).label("row_count")) \
        .filter(Hashes.cracked == '1') \
        .filter(Hashes.recovered_at > date_start) \
        .filter(Hashes.recovered_at < date_end) \
        .filter(or_(Hashes.hash_type == 7500, Hashes.hash_type == 13100, Hashes.hash_type == 18200, Hashes.hash_type == 19600, Hashes.hash_type == 19700, Hashes.hash_type == 19800, Hashes.hash_type == 19900)) \
        .group_by(Hashes.recovered_by) \
        .order_by(func.count(Hashes.id).desc()) \
        .all() 
    
    total_kerberos_recovered_personal_pct = 0
    for entry in total_kerberos_recovered_all:
        if entry.recovered_by == current_user.id:
            total_kerberos_recovered_personal_pct = round(entry.row_count / (len(total_kerberos_recovered_all)-1), 2) * 100

    # Personal Kerberos
    total_kerberos_recovered_personal_cnt = db.session.query(Hashes.id) \
        .filter(Hashes.cracked == '1') \
        .filter(Hashes.recovered_at > date_start) \
        .filter(Hashes.recovered_at < date_end) \
        .filter(Hashes.recovered_by == current_user.id) \
        .filter(or_(Hashes.hash_type == 7500, Hashes.hash_type == 13100, Hashes.hash_type == 18200, Hashes.hash_type == 19600, Hashes.hash_type == 19700, Hashes.hash_type == 19800, Hashes.hash_type == 19900)) \
        .count()

    # Most effective task
    #select count(h.id),t.name from hashes as h join tasks as t on t.id = h.task_id where h.task_id is not NULL and h.task_id != '0' and recovered_at > '2025-01-01' group by h.task_id order by count(h.id) DESC LIMIT 10;
    most_effective_tasks_raw = db.session.query(func.count(Hashes.id).label("row_count"), Tasks.name, Users.email_address).join(Tasks, Hashes.task_id == Tasks.id).join(Users, Tasks.owner_id==Users.id) \
        .filter(Hashes.cracked == '1') \
        .filter(Hashes.recovered_at > date_start) \
        .filter(Hashes.recovered_at < date_end) \
        .filter(Hashes.task_id is not None) \
        .group_by(Hashes.task_id) \
        .order_by(func.count(Hashes.id).desc()) \
        .limit(10) \
        .all()
    
    most_effective_tasks_table = []
    for entry in most_effective_tasks_raw:
        dict_entry = {}
        dict_entry['count'] = entry.row_count
        dict_entry['task_name'] = entry.name
        dict_entry['task_author'] = entry.email_address
        most_effective_tasks_table.append(dict_entry)

    # Most effective tasks for hashtype 1000:
    #select count(h.id),t.name from hashes as h join tasks as t on t.id = h.task_id where h.task_id is not NULL and h.task_id != '0' and recovered_at > '2025-01-01' and h.hash_type='1000' group by h.task_id order by count(h.id) DESC LIMIT 10;
    most_effective_tasks_1000_raw = db.session.query(func.count(Hashes.id).label("row_count"), Tasks.name, Users.email_address).join(Tasks, Hashes.task_id == Tasks.id).join(Users, Tasks.owner_id==Users.id) \
        .filter(Hashes.cracked == '1') \
        .filter(Hashes.recovered_at > date_start) \
        .filter(Hashes.recovered_at < date_end) \
        .filter(Hashes.task_id is not None) \
        .filter(Hashes.hash_type == 1000) \
        .group_by(Hashes.task_id) \
        .order_by(func.count(Hashes.id).desc()) \
        .limit(10) \
        .all()
    
    most_effective_tasks_1000_table = []
    for entry in most_effective_tasks_1000_raw:
        dict_entry = {}
        dict_entry['count'] = entry.row_count
        dict_entry['task_name'] = entry.name
        dict_entry['task_author'] = entry.email_address
        most_effective_tasks_1000_table.append(dict_entry)

    # Most effective tasks for hashtype 5600
    #select count(h.id),t.name from hashes as h join tasks as t on t.id = h.task_id where h.task_id is not NULL and h.task_id != '0' and recovered_at > '2025-01-01' and h.hash_type='5600' group by h.task_id order by count(h.id) DESC LIMIT 10;
    most_effective_tasks_5600_raw = db.session.query(func.count(Hashes.id).label("row_count"), Tasks.name, Users.email_address).join(Tasks, Hashes.task_id == Tasks.id).join(Users, Tasks.owner_id==Users.id) \
        .filter(Hashes.cracked == '1') \
        .filter(Hashes.recovered_at > date_start) \
        .filter(Hashes.recovered_at < date_end) \
        .filter(Hashes.task_id is not None) \
        .filter(or_(Hashes.hash_type == 5500, Hashes.hash_type == 5600, Hashes.hash_type == 27000, Hashes.hash_type == 27100)) \
        .group_by(Hashes.task_id) \
        .order_by(func.count(Hashes.id).desc()) \
        .limit(10) \
        .all()
    
    most_effective_tasks_5600_table = []
    for entry in most_effective_tasks_5600_raw:
        dict_entry = {}
        dict_entry['count'] = entry.row_count
        dict_entry['task_name'] = entry.name
        dict_entry['task_author'] = entry.email_address
        most_effective_tasks_5600_table.append(dict_entry)

    # Most effective tasks for hashtype 13100
    #select count(h.id),t.name from hashes as h join tasks as t on t.id = h.task_id where h.task_id is not NULL and h.task_id != '0' and recovered_at > '2025-01-01' and h.hash_type='13100' group by h.task_id order by count(h.id) DESC LIMIT 10;
    most_effective_tasks_13100_raw = db.session.query(func.count(Hashes.id).label("row_count"), Tasks.name, Users.email_address).join(Tasks, Hashes.task_id == Tasks.id).join(Users, Tasks.owner_id==Users.id) \
        .filter(Hashes.cracked == '1') \
        .filter(Hashes.recovered_at > date_start) \
        .filter(Hashes.recovered_at < date_end) \
        .filter(Hashes.task_id is not None) \
        .filter(or_(Hashes.hash_type == 7500, Hashes.hash_type == 13100, Hashes.hash_type == 18200, Hashes.hash_type == 19600, Hashes.hash_type == 19700, Hashes.hash_type == 19800, Hashes.hash_type == 19900)) \
        .group_by(Hashes.task_id) \
        .order_by(func.count(Hashes.id).desc()) \
        .limit(10) \
        .all()
    
    most_effective_tasks_13100_table = []
    for entry in most_effective_tasks_13100_raw:
        dict_entry = {}
        dict_entry['count'] = entry.row_count
        dict_entry['task_name'] = entry.name
        dict_entry['task_author'] = entry.email_address
        most_effective_tasks_13100_table.append(dict_entry)


    # Total hash_types recovered all
    # select COUNT(id),hash_type from hashes where cracked = '1' and recovered_at > '2025-01-01' group by hash_type order by count(id) DESC limit 10;

    return render_template('wrapped.html', title='Hashview Wrapped', 
                           previous_year = year,
                           longest_password_all_table=longest_password_all_table,
                           longest_password_personal=longest_password_personal,
                           longest_password_personal_rank=longest_password_personal_rank,
                           longest_password_all_cnt=longest_password_all_cnt,
                           most_passwords_recovered_all_table=most_passwords_recovered_all_table,
                           total_passwords_recovered_personal_cnt=total_passwords_recovered_personal_cnt,
                           total_passwords_recovered_personal_pct=total_passwords_recovered_personal_pct,
                           total_ntlm_recovered_personal_cnt=total_ntlm_recovered_personal_cnt,
                           total_ntlm_recovered_personal_pct=total_ntlm_recovered_personal_pct,
                           total_ntlm_recovered_all_table=total_ntlm_recovered_all_table,
                           total_ntlmv2_recovered_personal_cnt=total_ntlmv2_recovered_personal_cnt,
                           total_ntlmv2_recovered_personal_pct=total_ntlmv2_recovered_personal_pct,
                           total_ntlmv2_recovered_all_table=total_ntlmv2_recovered_all_table,    
                           total_kerberos_recovered_personal_cnt=total_kerberos_recovered_personal_cnt,
                           total_kerberos_recovered_personal_pct=total_kerberos_recovered_personal_pct,
                           total_kerberos_recovered_all_table=total_kerberos_recovered_all_table,                          
                           most_effective_tasks_table=most_effective_tasks_table,
                           most_effective_tasks_1000_table=most_effective_tasks_1000_table,
                           most_effective_tasks_5600_table=most_effective_tasks_5600_table,
                           most_effective_tasks_13100_table=most_effective_tasks_13100_table
                           )