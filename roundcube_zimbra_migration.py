from subprocess import Popen, PIPE, STDOUT
import os
import yaml

'''This imports user email from maildor folders to zimbra
Taking advantage of the fact that subfolders are stored in Maildir in the root folders like this:
.<folder>.<subfolder>.<subusbfolder>
'''

def zmcreatefolder(path=set()):
    '''Recursively creates a folder in zimbra'''

    if len(path) == 0:
        return 1
    if len(path) > 1:
        zmcreatefolder(path[:-1])
    print '      Creating folder {}'.format('/'.join(path))
    command = '{} -z -m {}@{}'.format( cfg['zmmbox'], user, domain)
    p = Popen(command.split(), stdout=PIPE, stdin=PIPE, stderr=STDOUT)
    command_out = p.communicate(input='createfolder "/{}"\n'.format('/'.join(path)))[0]
    print(command_out.decode())

def zmimportmail(src='', dst=''):
    '''Import mails from specified folder to specified zimbra mailbox/path
    Takes care of cur/new'''

    print '      Importing from {}/cur'.format(src)

    listdir = os.listdir(src)
    if 'cur' in listdir and os.listdir('{}/cur'.format(src)):
        command = '{} -z -m {}@{}'.format(cfg['zmmbox'], user, domain)
        print '        command is {}'.format(command)
        p = Popen(command.split(), stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        command_out = p.communicate(input='addMessage --noValidation "{}" "{}/cur"\n'.format(dst, src))[0]
        print(command_out.decode())
    else:
        print '        Empty. Skipping'
    print '      Importing from {}/new'.format(src)
    if 'new' in listdir and os.listdir('{}/new'.format(src)):
        command = '{} -z -m {}@{}'.format(cfg['zmmbox'], user, domain)
        print '        command is {}'.format(command)
        p = Popen(command.split(), stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        command_out = p.communicate(input='addMessage --noValidation "{}" "{}/new"\n'.format(dst, src))[0]
        print(command_out.decode())
    else:
        print '        Empty. Skipping'


# read configuration file
with open('roundcube_zimbra_migration.yaml', 'r') as ymlfile:
    cfg = yaml.load(ymlfile)
if len(cfg['suffix']) > 0:
    cfg['suffix'] = '{}/'.format(cfg['suffix'])

# get list of domains
domainlist = os.walk(cfg['importdir']).next()[1]
for domain in domainlist:
    print 'Processing domain: \033[95m{}\033[0m'.format(domain)

    # get list of users in current domain
    domainfolder ='/'.join([cfg['importdir'], domain])
    userlist = os.walk(domainfolder).next()[1]
    for user in userlist:
        print '  Processing user: \033[93m{}\033[0m'.format(user)
        userfolder = '/'.join([domainfolder, user, cfg['intermediate']])
        # import root folder
        if len(cfg['suffix']) > 0:
            zmcreatefolder(cfg['suffix'])
            zmimportmail(userfolder, '{}/{}'.format(cfg['suffix'], cfg['substitutions']['inbox']['new']))
        else:
            zmimportmail(userfolder, '/{}'.format(cfg['substitutions']['inbox']['new']))
        # get list of folders for current user
        folderlist = os.walk(userfolder).next()[1]
        for folder in folderlist:
            # skip known folders
            if folder in ('cur', 'new', 'tmp'):
                continue
            print '    Processing folder: \033[94m{}\033[0m'.format(folder)

            # check for substitutions before creating folders
            folder_new = folder
            for substitution in cfg['substitutions']:
                for substitution_old in cfg['substitutions'][substitution]['old']:
                    folder_new = folder_new.replace(substitution_old, cfg['substitutions'][substitution]['new'])
            # check for new folders still starting with dot
            if folder_new.startswith('.'):
                folder_new = folder_new.replace('.', '', 1)
            folder_new = '{}{}'.format(cfg['suffix'], folder_new.replace('.', '/'))
            print '      Creating: \033[92m{}\033[0m'.format(folder_new)
            print '      Importing from: \033[94m{}\033[0m to: \033[92m{}\033[0m'.format(folder, folder_new)
            zmcreatefolder(folder_new.split('/'))
            zmimportmail('/'.join([userfolder, folder]), folder_new)

