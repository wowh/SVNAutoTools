#-*-coding:UTF-8-*-
import ast
import os
import pysvn
import re
import shutil
import urllib
from Common import get_log_message
from Common import get_login
from Common import set_externals
from Common import set_log_message
from Common import test_url

version = '2.0.39'
baselib_rev = 0 
efmweb_rev = 0
efm_rev = 0
efmprotocols_trunk_url = 'http://192.168.1.225/svn/ComponentProductLine/branches/EFMProtocols'
efmprotocols_rls_url_format ='http://192.168.1.225/svn/ComponentProductLine/branches/release/EFMProtocols/EFMProtocols_V%s'
efmprotocols_rls_url = None
efmweb_trunk_url = 'http://192.168.1.225/svn/WebProductLine/branches/EFMWeb'
efmweb_rls_url_format = 'http://192.168.1.225/svn/WebProductLine/branches/release/EFMWeb/EFMWeb_V%s'
efmweb_rls_url = None
efm_trunk_url = 'http://192.168.1.225/svn/PlatFormProductLine/branches/EFMUDC'
efm_rls_url_format = 'http://192.168.1.225/svn/PlatFormProductLine/branches/release/EFMUDC/EFMUDC_V%s'
efm_rls_url = None

def get_revison_from_jenkins(url):
	global baselib_rev
	global efmweb_rev
	global efm_rev
	try:
		jenkins_build_info = ast.literal_eval(urllib.urlopen(url).read())
		revisions = jenkins_build_info['changeSet']['revisions']
		for revision_info in revisions:
			module = revision_info['module']
			revision = (int)(revision_info['revision'])
			if efmprotocols_trunk_url in module:
				baselib_rev = revision
				if revision > baselib_rev: 
					baselib_rev = revision
					pass
			elif module == efmweb_trunk_url:
				efmweb_rev = revision 
			elif module == efm_trunk_url:
				efm_rev = revision

		if efmweb_rev > 0 and efm_rev > 0 and baselib_rev > 0:
			return True
		else:
			print "Get revision failed missing some revisions"
	except Exception, e:
		print "Get revision failed exception: %s"%str(e)
		return False

def get_revisons():
	global baselib_rev
	global efmweb_rev
	global efm_rev
	build_number = raw_input("jenkins build number:")
	url = 'http://192.168.1.51/jenkins/job/EFM_Baseline/%s/api/python?pretty=true'%build_number.strip()
	ret = get_revison_from_jenkins(url)
	if ret == False:
		baselib_rev = (int)(raw_input("Please input baselib revision:"))
		efmweb_rev = (int)(raw_input("Please input efmweb revision:"))
		efm_rev = (int)(raw_input("Please input efmudc revision:"))

	print "efm revisions efmudc:%d base_lib:%d efmweb:%d"%(efm_rev, baselib_rev, efmweb_rev)

def get_version():
	global version
	global efmprotocols_rls_url
	global efmweb_rls_url
	global efm_rls_url
	version = raw_input("Please input version:")
	while True:
		match = re.match('^[0-9]+.[0-9].[0-9]+$', version)
		if match != None:
			break
		version = raw_input("Invalid version please input again:")
		pass
	efmprotocols_rls_url = efmprotocols_rls_url_format%version
	efmweb_rls_url = efmweb_rls_url_format%version
	efm_rls_url = efm_rls_url_format%version
	print "EFMUDC_V%s will be created"%version

def create_branches(client):
	print "Begin create EFMProtocols release branch"
	if not test_url(client, efmprotocols_rls_url):
		set_log_message(u'建立EFMProtocols_V%s分支'%(version))
		client.copy(efmprotocols_trunk_url, 
			        efmprotocols_rls_url,
			        pysvn.Revision(pysvn.opt_revision_kind.number, baselib_rev))
		print "EFMProtocols_V%s create success"%version
	else:
		print "EFMProtocols_V%s create failed(already created)"%version

	print "Begin create EFMWeb release branch"
	if not test_url(client, efmweb_rls_url):
		set_log_message(u'建立EFMWeb_V%s分支'%(version))
		client.copy(efmweb_trunk_url, 
			        efmweb_rls_url,
			        pysvn.Revision(pysvn.opt_revision_kind.number, efmweb_rev))
		print "EFMWeb_V%s create success"%version
	else:
		print "EFMWeb_V%s create failed(already created)"%version

	print "Begin create EFMUDC release branch"
	if not test_url(client, efm_rls_url):
		set_log_message(u'建立EFMUDC_V%s分支'%version)
		client.copy(efm_trunk_url,
					efm_rls_url,
					pysvn.Revision(pysvn.opt_revision_kind.number, efm_rev))
		print "EFMUDC_V%s create success"%version
	else:
		print "EFMUDC_V%s create failed(already created)"%version

def change_efm_externals(client):
	if os.path.exists('tmp'):
		shutil.rmtree('tmp')

	os.mkdir('tmp')

	efm_rls_baselib_url = efm_rls_url + '/baselib'
	client.checkout(efm_rls_baselib_url, 'tmp/efmudc_baselib', False)

	efmprotocols_rls_include_url = efmprotocols_rls_url + '/include' 
	efmprotocols_rls_lib_url = efmprotocols_rls_url + '/lib'
	externals_values = [(efmprotocols_rls_include_url, 'include'), (efmprotocols_rls_lib_url, 'lib')]
	if set_externals(client, 'tmp/efmudc_baselib', externals_values) == True:
		print "Commit externals of baselib"
		client.checkin('tmp/efmudc_baselib', u'修改对应发布分支')
	else:
		print "No change of baselib externals found"

	efm_rls_web_url = efm_rls_url + '/web'
	client.checkout(efm_rls_web_url, 'tmp/efmweb', False)
	externals_values = [(efmweb_rls_url, 'EFMWeb')]
	if set_externals(client, 'tmp/efmweb', externals_values) == True:
		print "Commit externals of efmweb"
		client.checkin('tmp/efmweb', u'修改对应发布分支')
	else:
		print "No change of efmweb externals found"

def main():
	get_revisons()
	get_version()

	client = pysvn.Client()
	client.callback_get_log_message = get_log_message
	client.callback_get_login = get_login

	create_branches(client)
	change_efm_externals(client)

if __name__ == '__main__':
	main()

