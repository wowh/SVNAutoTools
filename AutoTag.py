#-*-coding:UTF-8-*-
import ast
import os
import pysvn
import re
import shutil
import sys
import urllib
from Common import get_log_message
from Common import get_login
from Common import set_externals
from Common import set_log_message
from Common import test_url

version = '2.0.39'
baselib_lib_rev = 0 
baselib_include_rev = 0
efmweb_rev = 0
efm_rev = 0
efmprotocols_lib_url = None
efmprotocols_include_url = None
efmweb_url = None
efm_url = None
efm_tag_base_url = 'http://192.168.1.225/svn/PlatFormProductLine/tags/EFMUDC'
tag_name = None

def get_revison_from_jenkins(url):
	global baselib_lib_rev
	global baselib_include_rev
	global efmweb_rev
	global efm_rev
	global efmprotocols_include_url
	global efmprotocols_lib_url
	global efmweb_url
	global efm_url
	try:
		jenkins_build_info = ast.literal_eval(urllib.urlopen(url).read())
		revisions = jenkins_build_info['changeSet']['revisions']
		for revision_info in revisions:
			module = revision_info['module']
			revision = (int)(revision_info['revision'])
			if 'EFMProtocols' in module:
				if 'lib' in module:
					efmprotocols_lib_url = module
					baselib_lib_rev = revision
					pass
				if 'include' in module:
					efmprotocols_include_url = module
					baselib_include_rev = revision
					pass
			elif 'EFMWeb' in module:
				efmweb_url = module
				efmweb_rev = revision 
			elif 'EFMUDC' in module:
				efm_url = module
				efm_rev = revision

		if efmweb_rev > 0 and efm_rev > 0 and baselib_include_rev > 0 and baselib_lib_rev > 0:
			return True
		else:
			print "Get revision failed missing some revisions"
	except Exception, e:
		print "Get revision failed exception: %s"%str(e)
		return False

def get_revisions():
	url = raw_input("jenkins page url:")
	ret = get_revison_from_jenkins(url)
	if ret == False:
		print "get revisions failed."
		sys.exit(1)

	print "get revisions success."
	print "efmudc:%s %d"%(efm_url, efm_rev)
	print "baselib_include:%s %d"%(efmprotocols_include_url, baselib_include_rev)
	print "baselib_lib:%s %d"%(efmprotocols_lib_url, baselib_lib_rev)
	print "efmweb:%s %d"%(efmweb_url, efmweb_rev)

def get_version():
	global version
	global tag_name
	version = raw_input("Please input version:")
	while True:
		match = re.match('^[0-9]+.[0-9](.[0-9]+){1,2}$', version)
		if match != None:
			break
		version = raw_input("Invalid version please input again:")
		pass
	tag_name = 'EFMUDC_V%s'%version
	print "EFMUDC_V%s will be created"%version

def create_tag(client):
	print "Begin create tag %s"%tag_name
	efm_tag_url = efm_tag_base_url + '/%s'%tag_name
	if not test_url(client, efm_tag_url):
		set_log_message('EFMUDC_V%s发布'%version)
		client.copy(efm_url, efm_tag_url, pysvn.Revision(pysvn.opt_revision_kind.number, efm_rev))
		print "EFMUDC_V%s create success"%version
	else:
		print "EFMUDC_V%s create failed(already created)"%version

def fix_revisions(client):
	if os.path.exists('tmp'):
		shutil.rmtree('tmp')

	os.mkdir('tmp')

	efm_tag_baselib_url = efm_tag_base_url + '/' + tag_name + '/baselib'
	client.checkout(efm_tag_baselib_url, 'tmp/efmudc_tag_baselib', False)
	externals_values = [('-r %d %s'%(baselib_include_rev, efmprotocols_include_url), 'include'),
						('-r %d %s'%(baselib_lib_rev, efmprotocols_lib_url), 'lib')]
	if set_externals(client, 'tmp/efmudc_tag_baselib', externals_values) == True:
		print "Commit externals of baselib"
		client.checkin("tmp/efmudc_tag_baselib", u'固定external版本')
	else:
		print "No change of baselib externals found"

	efm_tag_web_url = efm_tag_base_url + '/' + tag_name + '/web'
	client.checkout(efm_tag_web_url, 'tmp/efmudc_tag_web', False)
	externals_values = [('-r %d %s'%(efmweb_rev, efmweb_url), 'EFMWeb')]
	if set_externals(client, 'tmp/efmudc_tag_web', externals_values):
		print "Commit externals of efmweb"
		client.checkin("tmp/efmudc_tag_web", u'固定external版本')
	else:
		print "No change of baselib externals found"

def main():
	get_revisions()
	get_version()

	client = pysvn.Client()
	client.callback_get_log_message = get_log_message
	client.callback_get_login = get_login

	create_tag(client)
	fix_revisions(client)

if __name__ == '__main__':
	main()


