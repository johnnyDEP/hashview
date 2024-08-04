"""Flask routes to handle Rules"""
import os
from flask import Blueprint, render_template, flash, url_for, redirect, current_app, request
from flask_login import login_required, current_user
from hashview.models import Rules, Tasks, Jobs, JobTasks, Users
from hashview.rules.forms import RulesForm, RulesEditForm
from hashview.utils.utils import save_file, get_linecount, get_filehash
from hashview.models import db


rules = Blueprint('rules', __name__)

#############################################
# Rules
#############################################

@rules.route("/rules", methods=['GET'])
@login_required
def rules_list():
    """Function to return list of rules"""
    rules = Rules.query.all()
    tasks = Tasks.query.all()
    jobs = Jobs.query.all()
    jobtasks = JobTasks.query.all()
    users = Users.query.all()
    return render_template('rules.html', title='Rules', rules=rules, tasks=tasks, jobs=jobs, jobtasks=jobtasks, users=users)

@rules.route("/rules/add", methods=['GET', 'POST'])
@login_required
def rules_add():
    """Function to rules file"""
    form = RulesForm()
    if form.validate_on_submit():
        if form.rules.data:
            rules_path = os.path.join(current_app.root_path, save_file('control/rules', form.rules.data))

            rule = Rules(   name=form.name.data,
                            owner_id=current_user.id,
                            path=rules_path,
                            size=get_linecount(rules_path),
                            checksum=get_filehash(rules_path))
            db.session.add(rule)
            db.session.commit()
            flash('Rules File created!', 'success')
            return redirect(url_for('rules.rules_list'))
    return render_template('rules_add.html', title='Rules Add', form=form)

@rules.route("/rules/edit/<int:rule_id>", methods=['GET', 'POST'])
@login_required
def rules_edit(rule_id):

    rules = Rules.query.get(rule_id)
    if not rules:
        flash('Invalid Rule File')
        return redirect(url_for('rules.rules_list'))

    if current_user.admin or rules.owner_id == current_user.id:

        form = RulesEditForm()
        if request.method == 'GET':
            with open(rules.path, "r") as file:
                S = file.read()

            form.name.data = rules.name
            form.content.data = S


        elif request.method == 'POST':

            if not form.name.data:
                flash('Rules file requires a name.')
                return redirect(url_for('rules.rules_edit'))
            if not form.content.data:
                flash('Rule data must be populated')
                return redirect(url_for(rules.rules_edit()))

            # remove old rules file
            os.remove(rules.path)

            # create new file
            rules_file = open(rules.path, 'w+')
            rules_file.write(form.content.data)
            rules_file.close()

            rules.name = form.name.data
            rules.size = get_linecount(rules.path)
            rules.checksum = get_filehash(rules.path)
            db.session.commit()

            flash('Rules updated', 'success')
        
    
        return render_template('rules_edit.html', title='Rules Edit', form=form, rules_name = rules.name)
    else:   
        flash('Unauthorzed Action!', 'danger')
        return redirect(url_for('rules.rules_list'))

@rules.route("/rules/delete/<int:rule_id>", methods=['GET', 'POST'])
@login_required
def rules_delete(rule_id):
    """Function to rules file"""
    rule = Rules.query.get(rule_id)
    if current_user.admin or rule.owner_id == current_user.id:
        # Check if part of a task
        tasks = Tasks.query.filter_by(rule_id=rule.id).first()
        if tasks:
            flash('Rules is currently used in a task and can not be delete.', 'danger')
        else:
            db.session.delete(rule)
            db.session.commit()
        flash('Rule file has been deleted!', 'success')
    else:
        flash('Unauthorized action!', 'danger')
    return redirect(url_for('rules.rules_list'))
