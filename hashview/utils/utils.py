"""Flask routes to handle utils"""
import os
import secrets
import hashlib
import re
import _md5
import requests
from datetime import datetime
from hashview.models import Rules, Wordlists, Hashfiles, HashfileHashes, Hashes, Tasks, Jobs, JobTasks, JobNotifications, Users, Agents, Customers
from flask import current_app, url_for
from hashview.models import db
from flask_mail import Message



def save_file(path, form_file):
    """Function to safe file from form submission"""

    random_hex = secrets.token_hex(8)
    file_name = random_hex + os.path.split(form_file.filename)[0] + '.txt'
    file_path = os.path.join(current_app.root_path, path, file_name)
    form_file.save(file_path)
    return file_path

def _count_generator(reader):
    b = reader(1024 * 1024)
    while b:
        yield b
        b = reader(1024 * 1024)

def get_linecount(filepath):
    """Function to return line count of file"""

    with open(filepath, 'rb') as fp:
        c_generator = _count_generator(fp.raw.read)
        count = sum(buffer.count(b'\n') for buffer in c_generator)
        return count + 1

def get_filehash(filepath):
    """Function to sha256 hash of file"""

    sha256_hash = hashlib.sha256()
    with open(filepath,"rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096),b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def notify_admins(subject, message):
    users = Users.query.filter_by(admin=True).all()

    for user in users:
        if user.pushover_app_id and user.pushover_user_key:
            send_pushover(user, subject, message)
        send_email(user, subject, message)

def send_email(user, subject, message):
    """Function to send email"""

    msg = Message(subject, recipients=[user.email_address])
    msg.body = message
    try:
        current_app.extensions['mail'].send(msg)
        return True
    except:
        return False

def send_html_email(user, subject, message):
    """Function to send html based email"""

    msg = Message(subject, recipients=[user.email_address])
    msg.html = message
    current_app.extensions['mail'].send(msg)

def send_pushover(user, subject, message):
    """Function to send pushover notification"""

    if not user.pushover_user_key:
        current_app.logger.info('SendPushover is Complete with Failure(User Key not Configured).')
        return

    if not user.pushover_app_id:
        current_app.logger.info('SendPushover is Complete with Failure(App Id not Configured).')
        return

    # https://pushover.net/api
    payload = dict(
        token   = user.pushover_app_id,
        user    = user.pushover_user_key,
        message = message,
        title   = subject,
    )
    response = requests.post('https://api.pushover.net/1/messages.json', params=payload, timeout=30)
    response_json = response.json()
    if 400 <= response.status_code < 500:
        current_app.logger.info('SendPushover is Complete with Failure(%s).', response_json.get('errors'))
        send_email(user, 'Error Sending Push Notification', f'Check your Pushover API keys in  your profile. Original Message: {message}')
        return

    current_app.logger.info('SendPushover is Complete with Success(%s).', response_json)
    return

def get_md5_hash(string):
    """Function to get md5 hash of string"""

    m = _md5.md5(string.encode('utf-8'))
    return m.hexdigest()

def import_hash_only(line, hash_type):
    """Function to import single hash"""

    hash = Hashes.query.filter_by(hash_type=hash_type, sub_ciphertext=get_md5_hash(line)).first()

    if hash:
        return hash.id

    new_hash = Hashes(hash_type=hash_type, sub_ciphertext=get_md5_hash(line), ciphertext=line, cracked=0)
    db.session.add(new_hash)
    db.session.commit()
    return new_hash.id

def import_hashfilehashes(hashfile_id, hashfile_path, file_type, hash_type):
    """Function to hashfile"""

    # Open file
    file = open(hashfile_path, 'r')
    lines = file.readlines()

    # for line in file,
    for line in lines:
        # If line is empty:
        username = None
        if len(line) > 0:
            if file_type == 'hash_only':
                # forcing lower casing of hash as hashcat will return lower cased version of the has and we want to match what we imported.
                if hash_type in ('300', '1731', '1000'):
                    hash_id = import_hash_only(line=line.lower().rstrip(), hash_type=hash_type)
                elif hash_type == '2100':
                    line = line.lower().rstrip()
                    line = line.replace('$dcc2$', '$DCC2$')
                    hash_id = import_hash_only(line, hash_type)
                else:
                    hash_id = import_hash_only(line=line.rstrip(), hash_type=hash_type)
                # extract username from dcc2 hash
                if hash_type == '2100':
                    username = line.split('#')[1]
                else:
                    username = None
            elif file_type == 'user_hash':
                if ':' in line:
                    if hash_type in ('300', '1731'):
                        hash_id = import_hash_only(line=line.lower().rstrip(), hash_type=hash_type)
                    if hash_type == '2100':
                        line = line.split(':',1)[1].rstrip()
                        line = line.lower()
                        line = line.replace('$dcc2$', '$DCC2$')
                        hash_id = import_hash_only(line, hash_type)
                        username = line.split(':')[0]
                    else:
                        hash_id = import_hash_only(line=line.split(':',1)[1].rstrip(), hash_type=hash_type)
                        username = line.split(':')[0]
                else:
                    return False
            elif file_type == 'shadow':
                hash_id= import_hash_only(line=line.split(':')[1], hash_type=hash_type)
                username = line.split(':')[0]
            elif file_type == 'pwdump':
                # do we let user select LM so that we crack those instead of NTLM?
                # First extracting usernames so we can filter out machine accounts
                if re.search("\$$", line.split(':')[0]):
                #if '$' in line.split(':')[0]:
                    continue
                else:
                    hash_id = import_hash_only(line=line.split(':')[3].lower(), hash_type='1000')
                    username = line.split(':')[0]
            elif file_type == 'kerberos':
                hash_id = import_hash_only(line=line.lower().rstrip(), hash_type=hash_type)
                if hash_type == '18200':
                    username = line.split('$')[3].split(':')[0]
                else:
                    username = line.split('$')[3]
            elif file_type == 'NetNTLM':
                # First extracting usernames so we can filter out machine accounts
                # 5600, domain is case sensitve. Hashcat returns username in upper case.
                if re.search("\$$", line.split(':')[0]):
                #if '$' in line.split(':')[0]:
                    continue
                else:
                    # uppercase uesrname in line
                    line_list = line.split(':')
                    # uppercase the username in line
                    line_list[0] = line_list[0].upper()
                    # lowercase the rest (except domain name) 3,4,5
                    line_list[3] = line_list[3].lower()
                    line_list[4] = line_list[4].lower()
                    line_list[5] = line_list[5].lower()
                    line = ':'.join(line_list)
                    hash_id = import_hash_only(line=line.rstrip(), hash_type=hash_type)
                    username = line.split(':', maxsplit=1)[0]
            else:
                return False
            if username is None:
                hashfilehashes = HashfileHashes(hash_id=hash_id, hashfile_id=hashfile_id)
            else:
                hashfilehashes = HashfileHashes(hash_id=hash_id, username=username.encode('latin-1').hex(), hashfile_id=hashfile_id)
            db.session.add(hashfilehashes)
            db.session.commit()

    return True

def update_dynamic_wordlist(wordlist_id):
    """Function to update dynamic wordlist"""

    wordlist = Wordlists.query.get(wordlist_id)
    hashes = Hashes.query.filter_by(cracked=True).distinct('plaintext')
    usernames = HashfileHashes.query.distinct('username')
    customers = Customers.query.distinct('name');
    

    # Do we delete the original file, or overwrite it?
    # if we overwrite, what happens if the new content has fewer lines than the previous file.
    # would this even happen? In most/all cases there will be new stuff to add.
    # is there a file lock on a wordlist when in use by hashcat? Could we just create a temp file and replace after generation?
    # Open file
    file = open(wordlist.path, 'wt')
    if 'Hashes' in wordlist.name:
        for entry in hashes:
            file.write(str(bytes.fromhex(entry.plaintext).decode('latin-1')) + '\n')
    elif 'Usernames' in wordlist.name:
        username_set = set()
        for entry in usernames:
            if entry.username:
                username_string = str(bytes.fromhex(entry.username).decode('latin-1'))
                if '\\' in username_string:
                    #print(username_string)
                    #print(username_string.split('\\')[0])
                    #print(username_string.split('\\')[1])
                    username_set.add(username_string.split('\\')[0])
                    username_set.add(username_string.split('\\')[1])
                    username_set.add(username_string)
                else:
                    username_set.add(username_string)
                    #print(username_string)
        for entry in username_set:
            file.write(entry + '\n')
    elif 'Customers' in wordlist.name:
        customer_set = set()
        for entry in customers:
            customer_set.add(entry.name.lower())
        for entry in customer_set:
            file.write(entry + '\n')
    file.close()

    # update line count
    wordlist.size = get_linecount(wordlist.path)
    # update file hash
    wordlist.checksum = get_filehash(wordlist.path)
    # update last update
    wordlist.last_updated = datetime.today()
    db.session.commit()

def build_hashcat_command(job_id, task_id):
    """Function to build the main hashcat cmd we use to crack"""

    hc_binpath = '@HASHCATBINPATH@'
    task = Tasks.query.get(task_id)
    job = Jobs.query.get(job_id)
    rules_file = Rules.query.get(task.rule_id)
    hashfilehashes_single_entry = HashfileHashes.query.filter_by(hashfile_id = job.hashfile_id).first()
    hashes_single_entry = Hashes.query.get(hashfilehashes_single_entry.hash_id)
    hash_type = hashes_single_entry.hash_type
    attackmode = task.hc_attackmode
    mask = task.hc_mask

    # Combinator
    wordlist = Wordlists.query.get(task.wl_id)
    # if attackmode == 1:
        
    #     print('unsupported combinator')
    # else:
    #     wordlist = Wordlists.query.get(task.wl_id)

    target_file = 'control/hashes/hashfile_' + str(job.id) + '_' + str(task.id) + '.txt'
    crack_file = 'control/outfiles/hc_cracked_' + str(job.id) + '_' + str(task.id) + '.txt'
    if wordlist:
        relative_wordlist_path = 'control/wordlists/' + wordlist.path.split('/')[-1]
    else:
        relative_wordlist_path = ''
    
    if attackmode == 1:
        wordlist_2 = Wordlists.query.get(task.wl_id_2)
        if wordlist_2:
            relative_wordlist_2_path = 'control/wordlists/' + wordlist.path.split('/')[-1]
        else:
            relative_wordlist_2_path = ''

    if rules_file:
        relative_rules_path = 'control/rules/' + rules_file.path.split('/')[-1]
    else:
        relative_rules_path = ''

    session = secrets.token_hex(4)

    # Build cmd
    cmd = hc_binpath
    cmd += ' -O -w 3'
    cmd += ' --session ' + session
    cmd += ' -m ' + str(hash_type)
    cmd += ' --potfile-disable'
    cmd += ' --status --status-timer=15'
    cmd += ' --outfile-format 1,3'
    cmd += ' --outfile ' + crack_file

    # Dictionary with optional rules
    if attackmode == 0:
        if isinstance(task.rule_id, int):
            cmd += ' -r ' + relative_rules_path + ' ' + target_file + ' ' + relative_wordlist_path
        else:
            cmd += ' ' + target_file + ' ' + relative_wordlist_path
    # combinator
    elif attackmode == 1:
        if isinstance(task.j_rule, str):
            j_rule = " -j '" + task.j_rule + "' "
        else:
            j_rule = ' '
        
        if isinstance(task.k_rule, str):
            k_rule = " -k '" + task.k_rule + "' "
        else:
            k_rule = ' '
        cmd += ' ' + ' -a 1 ' + target_file + ' ' + relative_wordlist_path + j_rule + relative_wordlist_path + k_rule
    # maskmode
    elif attackmode == 3:
        cmd += ' ' + ' -a 3 ' + target_file + ' ' + mask
    # Hybrid (Wordlist + Mask)
    elif attackmode == 6:
        cmd += ' ' + ' -a 6 ' + target_file + ' ' + relative_wordlist_path + ' ' + mask
    elif attackmode == 7:
        cmd += ' ' + ' -a 7 ' + target_file + ' ' + mask + ' ' + relative_wordlist_path

    # Mask mode
    #if attackmode == 'bruteforce':
    #    cmd = hc_binpath + ' -O -w 3 ' + ' --session ' + session + ' -m ' + str(hash_type) + ' --potfile-disable' + ' --status --status-timer=15' + ' --outfile-format 1,3' + ' --outfile ' + crack_file + ' ' + ' -a 3 ' + target_file
    # elif attackmode == 'maskmode':
    #     cmd = hc_binpath + ' -O -w 3 ' + ' --session ' + session + ' -m ' + str(hash_type) + ' --potfile-disable' + ' --status --status-timer=15' + ' --outfile-format 1,3' + ' --outfile ' + crack_file + ' ' + ' -a 3 ' + target_file + ' ' + mask
    # elif attackmode == 'dictionary':
    #     if isinstance(task.rule_id, int):
    #         cmd = hc_binpath + ' -O -w 3 ' + ' --session ' + session + ' -m ' + str(hash_type) + ' --potfile-disable' + ' --status --status-timer=15' + ' --outfile-format 1,3' + ' --outfile ' + crack_file + ' ' + ' -r ' + relative_rules_path + ' ' + target_file + ' ' + relative_wordlist_path
    #     else:
    #         cmd = hc_binpath + ' -O -w 3 ' + ' --session ' + session + ' -m ' + str(hash_type) + ' --potfile-disable' + ' --status --status-timer=15' + ' --outfile-format 1,3' + ' --outfile ' + crack_file + ' ' + target_file + ' ' + relative_wordlist_path
    # elif attackmode == 'combinator':
    #   cmd = hc_binpath + ' -O -w 3 ' + ' --session ' + session + ' -m ' + str(hash_type) + ' --potfile-disable' + ' --status --status-timer=15' + ' --outfile-format 1,3' + ' --outfile ' + crack_file + ' ' + ' -a 1 ' + target_file + ' ' + wordlist_one.path + ' ' + ' ' + wordlist_two.path + ' ' + relative_rules_path

    return cmd

def update_job_task_status(jobtask_id, status):
    """Function to update task status of a job"""

    jobtask = JobTasks.query.get(jobtask_id)

    if jobtask is None:
        return False

    jobtask.status = status
    if status == 'Completed':
        jobtask.agent_id = None
        agent = Agents.query.get(jobtask.agent_id)
        if agent:
            agent.hc_status = ''
    db.session.commit()

    # Update Jobs
    # TODO
    # Shouldn't we be changing the job stats to match the jobtask status?
    # Add started at time
    job = Jobs.query.get(jobtask.job_id)
    if job.status == 'Queued':
        job.status = 'Running'
        job.started_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()

    # TODO
    # This is such a janky way of doing this. Instead of having the agent tell us its done, we're just assuming
    # That if no other tasks are active we must be done
    done = True
    jobtasks = JobTasks.query.filter_by(job_id=job.id).all()
    for jobtask in jobtasks:
        if jobtask.status == 'Queued' or jobtask.status == 'Running' or jobtask.status == 'Importing':
            done = False

    if done:
        job.status = 'Completed'
        job.ended_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()

        start_time = datetime.strptime(str(job.started_at), '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(str(job.ended_at), '%Y-%m-%d %H:%M:%S')
        durration = abs(end_time - start_time).seconds # So dumb you cant conver this to minutes, only resolution is seconds or days :(

        hashfile = Hashfiles.query.get(job.hashfile_id)
        hashfile.runtime += durration
        db.session.commit()

        # TODO
        # mark all jobtasks as completed
        job_notifications = JobNotifications.query.filter_by(job_id = job.id)

        # Send Notifications
        for job_notification in job_notifications:
            user = Users.query.get(job_notification.owner_id)
            cracked_cnt = db.session.query(Hashes).outerjoin(HashfileHashes, Hashes.id==HashfileHashes.hash_id).filter(Hashes.cracked == '1').filter(HashfileHashes.hashfile_id==job.hashfile_id).count()
            uncracked_cnt = db.session.query(Hashes).outerjoin(HashfileHashes, Hashes.id==HashfileHashes.hash_id).filter(Hashes.cracked == '0').filter(HashfileHashes.hashfile_id==job.hashfile_id).count()
            if job_notification.method == 'email':
                send_html_email(user, 'Hashview Job: "' + job.name + '" Has Completed!', 'Your job has completed. It ran for ' + getTimeFormat(durration) + ' and resulted in a total of ' + str(cracked_cnt) + ' out of ' + str(cracked_cnt+uncracked_cnt) + ' hashes being recovered! <br /><br /> <a href="' + url_for('analytics.get_analytics',customer_id=job.customer_id,hashfile_id=job.hashfile_id, _external=True) + '">View Analytics</a>')
            elif job_notification.method == 'push':
                if user.pushover_user_key and user.pushover_app_id:
                    send_pushover(user, 'Message from Hashview', 'Hashview Job: "' + job.name + '" Has Completed!')
                else:
                    send_email(user, 'Hashview: Missing Pushover Key', 'Hello, you were due to recieve a pushover notification, but because your account was not provisioned with an pushover ID and Key, one could not be set. Please log into hashview and set these options under Manage->Profile.')
            db.session.delete(job_notification)
            db.session.commit()

    return True

def validate_pwdump_hashfile(hashfile_path, hash_type):
    """Function to validate if hashfile submitted is a pwdump format"""

    file = open(hashfile_path, 'r')
    lines = file.readlines()
    line_number = 0

    for line in lines:
        line_number += 1

        # Skip entries that are just newlines
        if len(line) > 50000:
            return 'Error line ' + str(line_number) + ' is too long. Line length: ' + str(len(line)) + '. Max length is 50,000 chars.'
        if len(line) > 0:
            if ':' not in line:
                return 'Error line ' + str(line_number) + ' is missing a : character. Pwdump file should include usernames.'
            # This is slow af :(
            colon_cnt = 0
            for char in line:
                if char == ':':
                    colon_cnt += 1
            if colon_cnt < 6:
                return 'Error line ' + str(line_number) + '. File does not appear to be be in a pwdump format.'
            if hash_type == '1000':
                if len(line.split(':')[3]) != 32:
                    return 'Error line ' + str(line_number) + ' has an invalid number of characters (' + str(len(line.rstrip())) + ') should be 32'
            else:
                return 'Sorry. The only Hash Type we support for PWDump files is NTLM'
    return False

def validate_netntlm_hashfile(hashfile_path):
    """Function to validate if hashfile submitted is a netntlm format"""

    file = open(hashfile_path, 'r')
    lines = file.readlines()
    line_number = 0

    # Do a whole file check if file_type is NetNTLM
    # If duplicate usernames exists return error
    # we could probably wrap this into the for loop below

    list_of_username_and_computers = []
    for line in lines:
        username_computer = (line.split(':')[0] + ':' + line.split(':')[2]).lower()
        if username_computer in list_of_username_and_computers:
            return 'Error: Duplicate usernames / computer found in hashfiles (' + str(username_computer) + '). Please only submit unique usernames / computer.'
        list_of_username_and_computers.append(username_computer)

    for line in lines:
        line_number += 1

        # Skip entries that are just newlines
        if len(line) > 50000:
            return 'Error line ' + str(line_number) + ' is too long. Line length: ' + str(len(line)) + '. Max length is 50,000 chars.'
        if len(line) > 0:
            if ':' not in line:
                return 'Error line ' + str(line_number) + ' is missing a : character. NetNTLM file should include usernames.'
            # This is slow af :(
            colon_cnt = 0
            for char in line:
                if char == ':':
                    colon_cnt += 1
            if colon_cnt < 5:
                return 'Error line ' + str(line_number) + '. File does not appear to be be in a NetNTLM format.'
    return False

def validate_kerberos_hashfile(hashfile_path, hash_type):
    """Function to validate if hashfile submitted is a kerberos format"""

    file = open(hashfile_path, 'r')
    lines = file.readlines()
    line_number = 0

    for line in lines:
        line_number += 1

        # Skip entries that are just newlines
        if len(line) > 50000:
            return 'Error line ' + str(line_number) + ' is too long. Line length: ' + str(len(line)) + '. Max length is 50,000 chars.'
        if len(line) > 0:
            if '$' not in line:
                return 'Error line ' + str(line_number) + ' is missing a $ character. kerberos file should include these.'
            dollar_cnt = 0
            # This is slow af :(
            for char in line:
                if char == '$':
                    dollar_cnt += 1

            if hash_type == '7500':
                if dollar_cnt != 6:
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Kerberos 5, etype 23, AS-REQ Pre-Auth (1)'
                if line.split('$')[1] != 'krb5pa':
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Kerberos 5, etype 23, AS-REQ Pre-Auth (2)'
                if line.split('$')[2] != '23':
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Kerberos 5, etype 23, AS-REQ Pre-Auth (3)'
            elif hash_type == '13100':
                if dollar_cnt != 7 and dollar_cnt != 8:
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Kerberos 5, etype 23, TGS-REP (1)'
                if line.split('$')[1] != 'krb5tgs':
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Kerberos 5, etype 23, TGS-REP (2)'
                if line.split('$')[2] != '23':
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Kerberos 5, etype 23, TGS-REP (3)'
            elif hash_type == '18200':
                if dollar_cnt != 4 and dollar_cnt != 5:
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Kerberos 5, etype 23, AS-REP (1)'
                if line.split('$')[1] != 'krb5asrep':
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Kerberos 5, etype 23, AS-REP (2)'
                if line.split('$')[2] != '23':
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Kerberos 5, etype 23, AS-REP (3)'
            elif hash_type == '19600':
                if dollar_cnt != 6 and dollar_cnt != 7:
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Kerberos 5, etype 17, TGS-REP (AES128-CTS-HMAC-SHA1-96) (1)'
                if line.split('$')[1] != 'krb5tgs':
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Kerberos 5, etype 17, TGS-REP (AES128-CTS-HMAC-SHA1-96) (2)'
                if line.split('$')[2] != '17':
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Kerberos 5, etype 17, TGS-REP (AES128-CTS-HMAC-SHA1-96) (3)'
            elif hash_type == '19700':
                if dollar_cnt != 6 and dollar_cnt != 7:
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Kerberos 5, etype 18, TGS-REP (AES256-CTS-HMAC-SHA1-96) (1)'
                if line.split('$')[1] != 'krb5tgs':
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Kerberos 5, etype 18, TGS-REP (AES256-CTS-HMAC-SHA1-96) (2)'
                if line.split('$')[2] != '18':
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Kerberos 5, etype 18, TGS-REP (AES256-CTS-HMAC-SHA1-96) (3)'
            elif hash_type == '19800':
                if dollar_cnt != 5 and dollar_cnt != 6:
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Kerberos 5, etype 17, Pre-Auth (1)'
                if line.split('$')[1] != 'krb5pa':
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Kerberos 5, etype 17, Pre-Auth (2)'
                if line.split('$')[2] != '17':
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Kerberos 5, etype 17, Pre-Auth (3)'
            elif hash_type == '19900':
                if dollar_cnt != 5 and dollar_cnt != 6:
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Kerberos 5, etype 18, Pre-Auth (1)'
                if line.split('$')[1] != 'krb5pa':
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Kerberos 5, etype 18, Pre-Auth (2)'
                if line.split('$')[2] != '18':
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Kerberos 5, etype 18, Pre-Auth (3)'
            else:
                return 'Sorry. The only suppported Hash Types are: 7500, 13100, 18200, 19600, 19700, 19800 and 19900.'
    return False

def validate_shadow_hashfile(hashfile_path, hash_type):
    """Function to validate if hashfile submitted is a shadow format"""

    file = open(hashfile_path, 'r')
    lines = file.readlines()
    line_number = 0

    for line in lines:
        line_number += 1

        # Skip entries that are just newlines
        if len(line) > 50000:
            return 'Error line ' + str(line_number) + ' is too long. Line length: ' + str(len(line)) + '. Max length is 50,000 chars.'
        if len(line) > 0:
            if ':' not in line:
                return 'Error line ' + str(line_number) + ' is missing a : character. shadow file should include usernames.'
            if hash_type == '1800':
                dollar_cnt = 0
                for char in line:
                    if char == '$':
                        dollar_cnt+=1
                if dollar_cnt != 3:
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Sha512 Crypt from a shadow file.'
                if '$6$' not in line:
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Sha512 Crypt from a shadow file.'
    return False

def validate_user_hash_hashfile(hashfile_path):
    """Function to validate if hashfile submitted is a user:hash format"""

    file = open(hashfile_path, 'r')
    lines = file.readlines()
    line_number = 0

    for line in lines:
        line_number += 1

        # Skip entries that are just newlines
        if len(line) > 50000:
            return 'Error line ' + str(line_number) + ' is too long. Line length: ' + str(len(line)) + '. Max length is 50,000 chars.'
        if len(line) > 0:
            if ':' not in line:
                return 'Error line ' + str(line_number) + ' is missing a : character. user:hash file should have just ONE of these'

    return

# Dumb way of doing this, we return with an error message if we have an issue with the hashfile
# and return false if hashfile is okay. :/ Should be the otherway around :shrug emoji:
def validate_hash_only_hashfile(hashfile_path, hash_type):
    """Function to validate if hashfile submitted is a hash only format"""

    file = open(hashfile_path, 'r')
    lines = file.readlines()

    line_number = 0
    # for line in file,
    for line in lines:
        line_number += 1

        # Skip entries that are just newlines
        if len(line) > 50000:
            return 'Error line ' + str(line_number) + ' is too long. Line length: ' + str(len(line)) + '. Max length is 50,000 chars.'
        if len(line) > 0:

            # Check hash types
            if hash_type in ('0', '22', '1000'):
                if len(line.rstrip()) != 32:
                    return 'Error line ' + str(line_number) + ' has an invalid number of characters (' + str(len(line.rstrip())) + ') should be 32'
            if hash_type == '122':
                if len(line.rstrip()) != 50:
                    return 'Error line ' + str(line_number) + ' has an invalid number of characters (' + str(len(line.rstrip())) + ') should be 50'
            if hash_type == '300':
                if len(line.rstrip()) != 40:
                    return 'Error line ' + str(line_number) + ' has an invalid number of characters (' + str(len(line.rstrip())) + ') should be 40'
            if hash_type == '500':
                if '$1$' not in line:
                    return 'Error line ' + str(line_number) + ' is not a valid md5Crypt, MD5 (Unix) or Cisco-IOS $1$ (MD5) hash'
            if hash_type == '1100':
                if ':' not in line:
                    return 'Error line ' + str(line_number) + ' is missing a : character. Domain Cached Credentials (DCC), MS Cache hashes should have one'
            if hash_type == '1800':
                dollar_cnt = 0
                for char in line:
                    if char == '$':
                        dollar_cnt+=1
                if dollar_cnt != 3:
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Sha512 Crypt.'
                if '$6$' not in line:
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Sha512 Crypt.'
            if hash_type == '2100':
                if '$' not in line:
                    return 'Error line ' + str(line_number) + ' is missing a $ character. DCC2 Hashes should have these'
                dollar_cnt = 0
                hash_cnt = 0
                for char in line:
                    if char == '$':
                        dollar_cnt += 1
                    if char == '#':
                        hash_cnt += 1
                if dollar_cnt != 2:
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: DCC2 MS Cache'
                if hash_cnt != 2:
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: DCC2 MS Cache'
            if hash_type == '2400':
                if len(line.rstrip()) != 18:
                    return 'Error line ' + str(line_number) + ' has an invalid number of characters (' + str(len(line.rstrip())) + ') should be 18'
            if hash_type == '2410':
                if ':' not in line:
                    return 'Error line ' + str(line_number) + ' is missing a : character. Cisco-ASA Hashes should have these.'
            if hash_type == '3200':
                if '$' not in line:
                    return 'Error line ' + str(line_number) + ' is missing a $ character. bcrypt Hashes should have these.'
                dollar_cnt = 0
                for char in line:
                    if char == '$':
                        dollar_cnt += 1
                if dollar_cnt != 3:
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: bcrypt'
            if hash_type == '5700':
                if len(line.rstrip()) != 43:
                    return 'Error line ' + str(line_number) + ' has an invalid number of characters (' + str(len(line.rstrip())) + ') should be 43'
            if hash_type == '7100':
                if '$' not in line:
                    return 'Error line ' + str(line_number) + ' is missing a $ character. Mac OSX 10.8+ ($ml$) hashes should have these.'
                dollar_cnt = 0
                for char in line:
                    if char == '$':
                        dollar_cnt += 1
                if dollar_cnt != 2:
                    return 'Error line ' + str(line_number) + '. Doesnt appear to be of the type: Mac OSX 10.8+ ($ml$)'
            if hash_type in ('9400', '9500', '9600'):
                if '$' not in line:
                    return 'Error line ' + str(line_number) + ' is missing a $ character. Office hashes require 2.'
                if '*' not in line:
                    return 'Error line ' + str(line_number) + ' is missing a * character. Office hashes require 6.'
                star_cnt = 0
                for char in line:
                    if char == '*':
                        star_cnt +=1
                if star_cnt != 7:
                    return 'Error line ' + str(line_number) + '. Does not appear to be of the type office.'              

    return False

def getTimeFormat(total_runtime): # Runtime in seconds
    """Function to convert seconds into, minutes, hours, days or weeks"""

    if total_runtime >= 604800:
        return str(round(total_runtime/604800)) + " week(s)"
    elif total_runtime >= 86400:
        return str(round(total_runtime/86400)) + " day(s)"
    elif total_runtime >= 3600:
        return str(round(total_runtime/3600)) + " hour(s)"
    elif total_runtime >= 60:
        return str(round(total_runtime/60)) + " minute(s)"
    elif total_runtime < 60:
        return "less then 1 minute"
