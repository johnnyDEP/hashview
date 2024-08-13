"""Flask routes to handle Rules"""
import csv
import io
from flask import Blueprint, render_template, redirect, url_for, request, flash, send_file
from flask_login import login_required
from hashview.searches.forms import SearchForm
from hashview.models import Customers, Hashfiles, HashfileHashes, Hashes
from hashview.models import db
from hashview import jinja_hex_decode

searches = Blueprint('searches', __name__)

@searches.route("/search", methods=['GET', 'POST'])
@login_required
def searches_list():
    """Function to return list of search results"""

    customers = Customers.query.all()
    hashfiles = Hashfiles.query.all()
    search_form = SearchForm()
    # TODO
    # We should be able to include Customers and Hashfiles in the following queries
    if search_form.validate_on_submit():
        if search_form.search_type.data == 'hash':
            results = db.session.query(Hashes, HashfileHashes).join(HashfileHashes, Hashes.id==HashfileHashes.hash_id).filter(Hashes.ciphertext==search_form.query.data).all()
        elif search_form.search_type.data == 'user':
            results = db.session.query(Hashes, HashfileHashes).join(HashfileHashes, Hashes.id==HashfileHashes.hash_id).filter(HashfileHashes.username.like('%' + search_form.query.data.encode('latin-1').hex() + '%')).all()
        elif search_form.search_type.data == 'password':
            results = db.session.query(Hashes, HashfileHashes).join(HashfileHashes, Hashes.id==HashfileHashes.hash_id).filter(Hashes.plaintext == search_form.query.data.encode('latin-1').hex()).all()
        else:
            flash('No results found', 'warning')
            return redirect(url_for('searches.searches_list'))
    elif request.args.get("hash_id"):
        results = db.session.query(Hashes, HashfileHashes).join(HashfileHashes, Hashes.id == HashfileHashes.hash_id).filter(Hashes.id == request.args.get("hash_id"))
        if results.first(): #Without a value in the search input the export button will not pass the form validation
            search_form.query.data = results.first()[0].ciphertext #All hashs should be the same, so set the search input as the first rows hash value
            search_form.search_type.data = 'hash' #Set the search type to hash
    else:
        customers = None
        results = None
    if not results and request.method == 'POST':
        flash('No results found', 'warning')

    if results and "export" in request.form: #Export Results
        return export_results(customers, results, hashfiles, search_form.export_type.data)

    return render_template('search.html.j2', title='Search', searchForm=search_form, customers=customers, results=results, hashfiles=hashfiles )

#Creating this in memory instead of on disk to avoid any extra cleanup. This can be changed later if files get too large
def export_results(customers, results, hashfiles, separator):
    """Function to export search results"""
    str_io = io.StringIO()
    separator = (',' if separator == "Comma" else ":")
    get_rows(str_io, customers, results, hashfiles, separator)
    byte_io = io.BytesIO()
    byte_io.write(str_io.getvalue().encode())
    byte_io.seek(0)
    str_io.close()
    return send_file(byte_io, download_name="search.txt", as_attachment=True)

#If this logic changes on in the html (search.html) it will need to change here as well
def get_rows(str_io, customers, results, hashfiles, separator):
    """Function to get rows for export search results"""

    writer = csv.writer(str_io,delimiter=separator)
    for entry in results:
        col = ["None"] #set the first column to none incase the customer is not returned
        for hashfile in hashfiles:
            if hashfile.id == entry[1].hashfile_id:
                for customer in customers:
                    if customer.id == hashfile.customer_id:
                        col[0] = customer.name # Customer

        if entry[1].username: # Username
            col.append(jinja_hex_decode(entry[1].username))
        else:
            col.append("None")

        col.append(entry[0].ciphertext) # Hash

        if entry[0].cracked: #Plaintext
            col.append(jinja_hex_decode(entry[0].plaintext))
        else:
            col.append("unrecovered")

        writer.writerow([col[0],col[1],col[2],col[3]])
    return str_io
