import os, os.path
import subprocess as sp
import paramiko

rjn_dict = {
        "user"    : 'tm3124',
        "passwrd" : 'Leicestertigers14',
        "cluster" : 'raijin.nci.org.au',
        "path"    : '/short/k96/apps/qcp/qcp',
        }

mcc_dict = {
        "user"    : 'zlsee3',
        "passwrd" : 'yetterday1313',
        "cluster" : 'msgln6.its.monash.edu',
        "path"    : '/nfs-tmp/chm3911/2013/zlsee3/SHARED/ZOE/qcp/qcp',
        }

mas_dict = {
        "user"    : 'zseeger',
        "passwrd" : 'yetterday1',
        "cluster" : 'm3.massive.org.au',
        "path"    : '/projects/sn29/apps/qcp/qcp',
        }

#nct_dict = {
#        user    : 'zoz',
#        passwrd : 'yetterday1313',
#        cluster : '118.138.233.101',
#        }

mon_dict = {
        "user"    : 'zseeger',
        "passwrd" : 'yetterday1',
        "cluster" : 'monarch.erc.monash.edu',
        "path"    : '/home/zseeger/sn29/apps/qcp/qcp',
        }

mgs_dict = {
        "user"    : 'zseeger',
        "passwrd" : 'yetterday1',
        "cluster" : 'magnus.pawsey.org.au',
        "path"    : '/group/pawsey0197/apps/source/qcp/qcp',
        }


def hosts_dicts():
    """ Return host machine name. """
    import sys
    import subprocess as sp

    hw = False

    hostName = sp.getoutput("hostname")

    hostDict = {
            'raijin' : rjn_dict,
            'msgln'  : mcc_dict,
            'm3'     : mas_dict,
            'magnus' : mgs_dict,
            'monarch': mon_dict,
            }

    cp_dicts = []
    for key, value in hostDict.items():
        if key in hostName:
            here_dict = value
        else:
            cp_dicts.append(value)

    return here_dict, cp_dicts

here_dict, cp_dicts = hosts_dicts()

# FOR CLUSTER IN CLUSTERS TO COPY TO
for cluster in cp_dicts:
    # SETUP CLIENT
    ssh = paramiko.SSHClient()
    ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
    # OPEN CONNECTION
    ssh.connect(cluster["cluster"], username=cluster["user"], password=cluster["passwrd"])
    sftp = ssh.open_sftp()
    print("Connected: " + cluster["cluster"])
    # LIST ALL FILES
    for File in os.listdir(here_dict["path"]):
        # MAKE SURE A FILE
        if os.path.isfile(File):
            # PUT FILE TO REMOTE HOST
            sftp.put(here_dict["path"] + "/" + File, cluster["path"] + "/" + File)
            cmd = "chmod 755 " + cluster["path"] + "/" + File
            (stdin, stdout, stderr) = ssh.exec_command(cmd)
            print("Copied:",File, here_dict["path"], cluster["path"])

    # CLOSE CONNECTION
    sftp.close()
    ssh.close()
    print("Disconnected: " + cluster["cluster"])


