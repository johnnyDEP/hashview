from flask import Blueprint, jsonify, redirect, request, send_from_directory, current_app, url_for
from hashview.models import Agents, JobTasks, Tasks, Wordlists, Rules, Jobs, Hashes, Hashfiles, HashfileHashes, Users, HashNotifications, Settings
from hashview.utils.utils import save_file, get_md5_hash, update_dynamic_wordlist, update_job_task_status, send_email, send_pushover, notify_admins
from hashview.models import db
from sqlalchemy.ext.declarative import DeclarativeMeta
from packaging import version
from datetime import datetime, timedelta
import hashview
import os
import json
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, redirect, request, send_from_directory, url_for
from sqlalchemy.ext.declarative import DeclarativeMeta
from packaging import version
from hashview.models import Agents, JobTasks, Tasks, Wordlists, Rules, Jobs, Hashes, HashfileHashes, Users, HashNotifications, Settings
from hashview.utils.utils import get_md5_hash, update_dynamic_wordlist, update_job_task_status, send_email, send_pushover
from hashview.models import db
import hashview

api = Blueprint('api', __name__)

#
# Yeah, i know its bad and should be converted to a legit REST API.
# This code should be considered tempoary as we work over the port.
# Ideally this will get replaced (along with the agent code) some time later
#

class AlchemyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data) # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)

def is_authorized(user, agent, request):
    """Function to authorize agent"""
    is_user = False # This needs to be revisited
    if request.cookies:
        if user_authorized(request.cookies.get('uuid')):
            return True
        if is_user is False:
            if agent_authorized(request.cookies.get('uuid')):
                return True
    else:
        return False

def user_authorized(uuid):
    """Function to validate user authorization"""
    user = Users.query.filter_by(api_key=uuid).first()
    if user:
        return True
    return False

def agent_authorized(uuid):
    """Function to validate agent authorization"""
    agent = Agents.query.filter_by(uuid=uuid).first()
    if agent:
        if agent.status == 'Online' or agent.status == 'Working' or agent.status == 'Idle' or agent.status == 'Authorized':
            return True
    return False

def update_heartbeat(uuid):
    """Function to update agent status in DB"""
    agent = Agents.query.filter_by(uuid=uuid).first()
    if agent:
        agent.src_ip = request.remote_addr
        agent.last_checkin = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()

def version_check(agent_version):
    """Function to validate agent version"""
    if agent_version:
        if version.parse(agent_version) < version.parse(hashview.__version__):
            return False
        return True
    else:
        return False

@api.route('/v1/not_authorized', methods=['GET', 'POST'])
def v1_api_unauthorized():
    """Function to send unauthorized message"""
    message = {
        'status': 200,
        'type': 'Error',
        'msg': 'Your agent is not authorized to work with this cluster.'
    }
    return jsonify(message)

@api.route('/v1/upgrade_required')
def v1_api_upgrade_required():
    """Function to send upgrade required message"""
    message = {
        'status': 426,
        'type': 'message',
        'msg': 'Version missmatch, update your agent!'
    }
    return jsonify(message)

@api.route('/v1/agents/heartbeat', methods=['POST'])
def v1_api_set_agent_heartbeat():
    """Route to handle agent updates"""
    # Get uuid
    uuid = request.cookies.get('uuid')
    if not version_check(request.cookies.get('agent_version')):
        return redirect("/v1/upgrade_required")

    settings = Settings.query.first()

    # Get agent from db
    agent = Agents.query.filter_by(uuid=uuid).first()
    if not agent:
        # no agent found, time to add it to our db
        new_agent = Agents( name = request.cookies.get('name'),
                        src_ip = request.remote_addr,
                        uuid = uuid,
                        status = 'Pending',
                        last_checkin = datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        db.session.add(new_agent)
        db.session.commit()
        message = {
            'status': 200,
            'type': 'message',
            'msg': 'Go Away'
        }
        return jsonify(message)

    update_heartbeat(uuid)
    if agent.status == 'Pending':
        # Agent exists, but has not ben activated. Update heartbeet and turn agent away
        update_heartbeat(uuid)
        message = {
            'status': 200,
            'type': 'message',
            'msg': 'Go Away'
        }
        return jsonify(message)

    # check if job_task
    agent_data = request.get_json()

    # Check authorization cookies
    if agent_data['agent_status'] == 'Working':
        agent.status = 'Working'

        # Check if task has exceeded maximum runtime
        job_task = JobTasks.query.filter_by(agent_id = agent.id).first()
        if not job_task or job_task.status == 'Canceled':
            message = {
                'status': 200,
                'type': 'message',
                'msg': 'Canceled',
            }
            return jsonify(message)

        if settings.max_runtime_tasks > 0 and datetime.strptime(str(job_task.started_at), '%Y-%m-%d %H:%M:%S') + timedelta(hours=settings.max_runtime_tasks) < datetime.now():
            update_job_task_status(job_task.id, 'Canceled')
            message = {
                'status': 200,
                'type': 'message',
                'msg': 'Canceled',
            }
            return jsonify(message)

        # check if job has exceeded maximum runtime
        job = Jobs.query.get(job_task.job_id)
        job_tasks = JobTasks.query.filter_by(job_id = job.id).all()
        if settings.max_runtime_jobs > 0 and datetime.strptime(str(job.started_at), '%Y-%m-%d %H:%M:%S') + timedelta(hours=settings.max_runtime_jobs) < datetime.now():
            job.status = 'Canceled'
            job.ended_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            for job_task in job_tasks:
                job_task.status = 'Canceled'
                job_task.agent_id = None
            db.session.commit()
            message = {
                'status': 200,
                'type': 'message',
                'msg': 'Canceled',
            }
            return jsonify(message)

        if agent_data['hc_status']:
            agent.hc_status = agent_data['agent_status']
            hc_status = str(agent_data['hc_status']).replace("\'", "\"")
            json_response = json.loads(hc_status)
            agent.benchmark = json_response['Speed #']
            agent.hc_status = str(agent_data['hc_status']).replace("\'", "\"")

        db.session.commit()

    if agent_data['agent_status'] == 'Idle':
        # Clear hc_status if we're idle
        agent.status = "Idle"
        agent.hc_status = ""
        db.session.commit()
        already_assigned_task = JobTasks.query.filter_by(agent_id = agent.id).first()
        if already_assigned_task != None:
            message = {
                'status': 200,
                'type': 'message',
                'msg': 'START',
                'job_task_id': already_assigned_task.id
            }
            return jsonify(message)

        # Get first unassigned jobtask and 'assign' it to this agent
        job_task_entry = JobTasks.query.filter_by(status = 'Queued').order_by(JobTasks.priority.desc(), JobTasks.id).first()
        if job_task_entry:
            job_task_entry.agent_id = agent.id
            job_task_entry.status = 'Running'
            job_task_entry.started_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            db.session.commit()
            message = {
                'status': 200,
                'type': 'message',
                'msg': 'START',
                'job_task_id': job_task_entry.id
            }
            return jsonify(message)
        update_heartbeat(uuid)
        message = {
            'status': 200,
            'type': 'message',
            'msg': 'OK'
        }
        return jsonify(message)

    update_heartbeat(uuid)
    message = {
        'status': 200,
        'type': 'message',
        'msg': 'OK'
    }
    return jsonify(message)

@api.route('/v1/rules', methods=['GET'])
def v1_api_get_rules():
    """Route to get list of rules"""
    if not is_authorized(user=True, agent=True, request=request):
        return redirect("/v1/not_authorized")

    update_heartbeat(request.cookies.get('uuid'))
    rules = Rules.query.all()
    message = {
        'status': 200,
        'rules': json.dumps(rules, cls=AlchemyEncoder)
    }
    return jsonify(message)

# serve a rules file
@api.route('/v1/rules/<int:rules_id>', methods=['GET'])
def v1_api_get_rules_download(rules_id):
    """Route to deliver rules to agent"""
    if not is_authorized(user=True, agent=True, request=request):
        return redirect("/v1/not_authorized")

    update_heartbeat(request.cookies.get('uuid'))
    rules = Rules.query.get(rules_id)
    rules_name = rules.path.split('/')[-1]
    cmd = "gzip -9 -k -c hashview/control/rules/" + rules_name + " > hashview/control/tmp/" + rules_name + ".gz"

    # What command injection?!
    # TODO
    os.system(cmd)
    return send_from_directory('control/tmp', rules_name + '.gz', mimetype = 'application/octet-stream')

# Provide wordlist info (really should be plural)
@api.route('/v1/wordlists', methods=['GET'])
def v1_api_get_wordlist():
    """Route to deliever list of wordlists to agent"""
    if not is_authorized(user=True, agent=True, request=request):
        return redirect("/v1/not_authorized")

    update_heartbeat(request.cookies.get('uuid'))
    wordlists = Wordlists.query.all()
    message = {
        'status': 200,
        'wordlists': json.dumps(wordlists, cls=AlchemyEncoder)
    }
    return jsonify(message)

# serve a wordlist
@api.route('/v1/wordlists/<int:wordlist_id>', methods=['GET'])
def v1_api_get_wordlist_download(wordlist_id):
    """Route to deliver wordlist to agent""" 
    if not is_authorized(user=True, agent=True, request=request):
        return redirect("/v1/not_authorized")

    update_heartbeat(request.cookies.get('uuid'))
    wordlist = Wordlists.query.get(wordlist_id)
    wordlist_name = wordlist.path.split('/')[-1]
    random_hex = secrets.token_hex(8)
    cmd = "gzip -9 -k -c hashview/control/wordlists/" + wordlist_name + " > hashview/control/tmp/" + wordlist_name + "_" + random_hex + ".gz"

    # What command injection?!
    # TODO
    os.system(cmd)
    return send_from_directory('control/tmp', wordlist_name + "_" + random_hex + ".gz", mimetype = 'application/octet-stream')

# Update Dynamic Wordlist
@api.route('/v1/updateWordlist/<int:wordlist_id>', methods=['GET'])
def v1_api_get_update_wordlist(wordlist_id):
    """Route to force update of dynamic wordlist"""    
    isUser = False
    if not is_authorized(user=True, agent=True, request=request):
        return redirect("/v1/not_authorized")

    update_heartbeat(request.cookies.get('uuid'))
    update_dynamic_wordlist(wordlist_id)
    message = {
        'status': 200,
        'type': 'message',
        'msg': 'OK'
    }
    return jsonify(message)

# force or restart a queue item
# used when agent goes offline and comes back online
# without a running hashcat cmd while task still assigned to them
@api.route('/v1/jobTasks/<int:job_task_id>', methods=['GET'])
def v1_api_get_queue_assignment(job_task_id):
    """Route to deliver get queue assignment"""    
    if not is_authorized(user=True, agent=True, request=request):
        return redirect("/v1/not_authorized")

    update_heartbeat(request.cookies.get('uuid'))

    # Get agent id from UUID
    agent = Agents.query.filter_by(uuid=request.cookies.get('uuid')).first()
    job_task = JobTasks.query.filter_by(agent_id=agent.id).first()

    message = {
        'status': 200,
        'job_task': json.dumps(job_task, cls=AlchemyEncoder)
    }
    return jsonify(message)

# Provide job info
@api.route('/v1/jobs/<int:job_id>', methods=['GET'])
def v1_api_get_job(job_id):
    """Route to deliver job to agent"""    
    if not is_authorized(user=True, agent=True, request=request):
        return redirect("/v1/not_authorized")

    update_heartbeat(request.cookies.get('uuid'))
    job = Jobs.query.get(job_id)

    message = {
        'status': 200,
        'job': json.dumps(job, cls=AlchemyEncoder)
    }
    return jsonify(message)

# Provide task info
@api.route('/v1/tasks/<int:task_id>', methods=['GET'])
def v1_api_get_task(task_id):
    """Route to deliver task to agent"""    
    if not is_authorized(user=True, agent=True, request=request):
        return redirect("/v1/not_authorized")

    update_heartbeat(request.cookies.get('uuid'))
    task = Tasks.query.get(task_id)
    message = {
        'status': 200,
        'task': json.dumps(task, cls=AlchemyEncoder)
    }
    return jsonify(message)

# generate and serve hashfile
@api.route('/v1/hashfiles/<int:hashfile_id>', methods=['GET'])
def v1_api_get_hashfile(hashfile_id):
    """Route to deliver hashfile to agent"""    
    if not is_authorized(user=True, agent=True, request=request):
        return redirect("/v1/not_authorized")

    update_heartbeat(request.cookies.get('uuid'))
    random_hex = secrets.token_hex(8)
    file_object = open('hashview/control/tmp/' + random_hex, 'w')

    # do a left join select to get our ciphertext hashes
    dbresults = db.session.query(Hashes, HashfileHashes).outerjoin(HashfileHashes, Hashes.id==HashfileHashes.hash_id).filter(Hashes.cracked == '0').filter(HashfileHashes.hashfile_id==hashfile_id).all()
    for result in dbresults:
        file_object.write(result[0].ciphertext + '\n')
    file_object.close()

    return send_from_directory('control/tmp/', random_hex)

# Upload Cracked Hashes
@api.route('/v1/uploadCrackFile/<int:task_id>/<int:hash_type>', methods=['POST'])
def v1_api_put_jobtask_crackfile_upload(task_id, hash_type):
    """Route to recieve recovered hashes"""
    if not is_authorized(user=False, agent=True, request=request):
        return redirect("/v1/not_authorized")

    update_heartbeat(request.cookies.get('uuid'))

    # TODO
    # We really should validate if task_id is legit
    
    # save to file
    file_contents = request.get_json()

    #for entry in lines:
    for entry in file_contents['file'].split('\n'):
        if ':' in entry:
            encoded_plaintext = entry.split(':')[-1]
            #plaintext = bytes.fromhex(encoded_plaintext.rstrip())
            plaintext = encoded_plaintext.rstrip().upper()
            elements = entry.split(':')
            # Remove cracked hash
            elements.pop()
            ciphertext = ':'.join(elements)

            #print('Plaintext: ' + str(bytes.fromhex(plaintext).decode('latin-1')))
            #print('Ciphertext: ' + str(ciphertext))

            record = Hashes.query.filter_by(hash_type=hash_type, sub_ciphertext=get_md5_hash(ciphertext), cracked='0').first()
            if record:
                try:
                    #record.plaintext = plaintext.decode('latin-1')
                    record.plaintext = plaintext
                    record.cracked = 1
                    #print('i should be updating the datetime')
                    record.recovered_at = datetime.today()
                    record.task_id = task_id
                    db.session.commit()
                except Exception as error:
                    print('Failed to import following cracked hash: ' + str(encoded_plaintext))
                    print('Reason: ' + str(error))

    # Send Hash Completion Notifications
    hash_notifications = HashNotifications.query.all()
    for hash_notification in hash_notifications:
        user = Users.query.get(hash_notification.owner_id)
        message = "Congratulations, a hash has been recovered!: \n\n"

        # Check if hash is cracked
        hash = Hashes.query.get(hash_notification.hash_id)
        if hash.cracked:

            message += 'You can check the results using the following link: ' + "\n"
            message += url_for('searches.searches_list', hash_id=hash.id, _external=True)
            if hash_notification.method == 'email':
                send_email(user, 'Hashview User Hash Recovered!', message)
            elif hash_notification.method == 'push':
                if user.pushover_user_key and user.pushover_app_id:
                    send_pushover(user, 'Message from Hashview', message)
            else:
                send_email(user, 'Hashview: Missing Pushover Key', 'Hello, you were due to recieve a pushover notification, but because your account was not provisioned with an pushover ID and Key, one could not be set. Please log into hashview and set these options under Manage->Profile.')
            db.session.delete(hash_notification)
            db.session.commit()

    message = {
        'status': 200,
        'type': 'message',
        'msg': 'OK'
    }
    return jsonify(message)

# Upload Cracked Hashes
@api.route('/v1/uploadCrackFile/<int:job_task_id>', methods=['POST'])
def v1_api_post_jobtask_crackfile_upload(job_task_id):
    if not isAuthorized(user=False, agent=True, request=request):
        return redirect("/v1/not_authorized")

    updateHeartbeat(request.cookies.get('uuid'))

    # TODO 
    # Validate calling agent is actually assigned jobtask

    # save to file
    file_contents = request.get_json()

    # Get Hashtype from job_task_id
    job_task = JobTasks.query.get(job_task_id)

    # Get Job from job_task
    job = Jobs.query.get(job_task.job_id)

    # Get hashfile from job
    hashfile = Hashfiles.query.get(job.hashfile_id)

    # Get hashfilehashes from hashfile
    hashfilehashes = HashfileHashes.query.filter_by(hashfile_id=hashfile.id).first()

    # Get single hash
    single_hash = Hashes.query.get(hashfilehashes.hash_id)

    hash_type = single_hash.hash_type

    #for entry in lines:
    for entry in file_contents['file'].split('\n'):
        if ':' in entry:
            encoded_plaintext = entry.split(':')[-1]
            plaintext = encoded_plaintext.rstrip().upper()
            elements = entry.split(':')
            # Remove cracked hash
            elements.pop()
            ciphertext = ':'.join(elements)

            #print('Plaintext: ' + str(bytes.fromhex(plaintext).decode('latin-1')))
            #print('Ciphertext: ' + str(ciphertext))

            record = Hashes.query.filter_by(hash_type=hash_type, sub_ciphertext=get_md5_hash(ciphertext), cracked='0').first()
            if record:
                try:
                    #record.plaintext = plaintext.decode('latin-1')
                    record.plaintext = plaintext
                    record.cracked = 1
                    #print('i should be updating the datetime')
                    record.recovered_at = datetime.today()
                    record.task_id = job_task.task_id
                    record.recovered_by = job.owner_id
                    db.session.commit()
                except Exception as error:
                    print('Failed to import following cracked hash: ' + str(encoded_plaintext))
                    print('Reason: ' + str(error))

    # Send Hash Completion Notifications
    hash_notifications = HashNotifications.query.all()
    for hash_notification in hash_notifications:
        user = Users.query.get(hash_notification.owner_id)
        message = "Congratulations, a hash has been recovered!: \n\n"

        # Check if hash is cracked
        hash = Hashes.query.get(hash_notification.hash_id)
        if hash.cracked:

            message += 'You can check the results using the following link: ' + "\n"
            message += url_for('searches.searches_list', hash_id=hash.id, _external=True)
            if hash_notification.method == 'email':
                send_email(user, 'Hashview User Hash Recovered!', message)
            elif hash_notification.method == 'push':
                if user.pushover_user_key and user.pushover_app_id:
                    send_pushover(user, 'Message from Hashview', message)
            else:
                send_email(user, 'Hashview: Missing Pushover Key', 'Hello, you were due to recieve a pushover notification, but because your account was not provisioned with an pushover ID and Key, one could not be set. Please log into hashview and set these options under Manage->Profile.')
            db.session.delete(hash_notification)
            db.session.commit()

    message = {
        'status': 200,
        'type': 'message',
        'msg': 'OK'
    }
    return jsonify(message)


# Get Hashtype
@api.route('/v1/getHashType/<int:hashfile_id>', methods=['GET'])
def v1_api_getHashType(hashfile_id):
    """Route to deliver hashtype to agent"""   
    if not is_authorized(user=True, agent=True, request=request):
        return redirect("/v1/not_authorized")

    update_heartbeat(request.cookies.get('uuid'))
    hashfile_hash = HashfileHashes.query.filter_by(hashfile_id = hashfile_id).first()
    hash = Hashes.query.get(hashfile_hash.hash_id)

    message = {
        'status': 200,
        'type': 'message',
        'msg': 'OK',
        'hash_type': hash.hash_type
    }
    return jsonify(message)

# Update JobTask status
@api.route('/v1/jobtask/status', methods=['POST'])
def v1_api_set_queue_jobtask_status():
    """Route to recieve jobtask status from agent"""

    if not is_authorized(user=False, agent=True, request=request):
        return redirect("/v1/not_authorized")

    update_heartbeat(request.cookies.get('uuid'))

    status_json = request.get_json()

    if update_job_task_status(jobtask_id = status_json['job_task_id'], status = status_json['task_status']):
        message = {
            'status': 200,
            'type': 'message',
            'msg': 'OK'
        }
    else:
        message = {
            'status': 500,
            'type': 'message',
            'msg': 'Error setting jobtask status. Detail: job_task_id='+str(status_json['job_task_id'])+' status='+str(status_json['task_status'])
        }
    return jsonify(message)

# Search
@api.route('/v1/search', methods=['POST'])
def v1_api_search():
    """Route to deliver search results to user"""    
    if not is_authorized(user=True, agent=False, request=request):
        return redirect("/v1/not_authorized")

    search_json = request.get_json()
    if search_json:
        # Right now we're only asking hash, in the future we may get requests to search by user or by plaintext
        if search_json['hash']:
            # we could search by subciphertext instead of ciphertext if things get slow.
            # subcipher text is indexed whereas ciphertext is not
            cracked_hash = Hashes.query.filter_by(cracked=True).filter_by(ciphertext=search_json['hash']).first()
            if cracked_hash:
                msg = {
                    'hash_type': cracked_hash.hash_type,
                    'hash': search_json['hash'],
                    'plaintext': bytes.fromhex(cracked_hash.plaintext).decode('latin-1')
                }
                message = {
                    'status': 200,
                    'type': 'message',
                    'msg': msg
                }
            else:
                message = {
                    'status': 200,
                    'type': 'message',
                    'msg': 'Search complete. No Results Found.'
                }
        else:
            message = {
                'status': 500,
                'type': 'message',
                'msg': 'Invalid Search'
            }
    else:
        message = {
            'status': 500,
            'type': 'message',
            'msg': 'Invalid Search'
        }            
    return jsonify(message)

# Error
@api.route('/v1/error', methods=['POST'])
def v1_api_error():
    if not is_authorized(user=False, agent=True, request=request):
        return redirect("/vi/not_authorized")

    uuid = request.cookies.get('uuid')
    agent = Agents.query.filter_by(uuid=uuid).first()
    message_json = request.get_json()

    subject = 'Error on ' + str(agent.name)
    message_body = message_json['error']

    notify_admins(subject, message_body)

    message = {
        'status': 200,
        'type': 'message',
        'msg': 'OK'
        }
    return jsonify(message)
