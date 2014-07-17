import pysvn

log_message = None

def set_log_message(message):
	global log_message
	log_message = message

def get_log_message():
    return True, log_message

def get_login( realm, username, may_save ):
	print "Login needed."
	username = raw_input("Username:") 
	password = raw_input("Password:")
	retcode = True
	save = True
	return retcode, username, password, save

def set_externals(client, dir, external_values):
	externals_propvalue = '\n'.join(['%s %s' % (extval[0], extval[1]) for extval in external_values])
	prev_external = client.propget('svn:externals', dir)[dir]
	if prev_external.strip() != externals_propvalue.strip():
		client.propset('svn:externals', externals_propvalue, dir)
		return True
	else:
		return False

def test_url(client, url):
    try:
        client.info2(url, depth=pysvn.depth.empty)
        return True
    except pysvn.ClientError, ce:
        if ('non-existent' in ce.args[0]) or ('Host not found' in ce.args[0]):
            return False
        else:
			raise ce