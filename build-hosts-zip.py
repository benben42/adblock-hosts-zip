import os
from datetime import date
from shutil import make_archive, rmtree

try:
    from requests import request
except:
    from subprocess import call
    call('pip install requests', shell=True)

my_list = 'https://raw.githubusercontent.com/benben42/adblock-hosts-zip/master/adblock_lists.txt'

local_list = 'adblock_lists.txt'

ad_lists_fallback = [
'https://pgl.yoyo.org/adservers/serverlist.php?hostformat=hosts&showintro=0&mimetype=plaintext', 
'https://dbl.oisd.nl',
'https://raw.githubusercontent.com/tomasko126/easylistczechandslovak/master/filters.txt', 
'https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts',
'https://adaway.org/hosts.txt',
'https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts',
'https://raw.githubusercontent.com/anoop142/miui-hosts/master/hosts'
]

update_binary = f'''#!/sbin/sh
export OUTFD="/proc/self/fd/$2"
ui_print() {{
    echo "ui_print ${{1}}" > "$OUTFD"
}}
ui_print "Zip updated: {date.today()} "
ui_print ""
ui_print "Updating hosts file..."
ui_print "Detecting system mountpoint..."
system_as_root=`getprop ro.build.system_root_image`
if [ "$system_as_root" == "true" ]; then
SYSTEM_MOUNT=/system_root
else
SYSTEM_MOUNT=/system
fi
ui_print "Mounting system..."
mount $SYSTEM_MOUNT
ui_print "Extracting temp files..."
cd /tmp; mkdir adblockhosts; cd adblockhosts;
unzip -o "$3"
ui_print "Copy hosts file..."
cp ./hosts $SYSTEM_MOUNT/etc/
cp ./hosts $SYSTEM_MOUNT/system/etc/
ui_print "Cleaning up..."
rm /tmp/adblockhosts -rf
ui_print "Done, unmounting system..."
umount $SYSTEM_MOUNT'''

def remove_empty_lines(filename):
    if not os.path.isfile(filename):
        print("{} does not exist ".format(filename))
        return
    with open(filename) as filehandle:
        lines = filehandle.readlines()
    with open(filename, 'w') as filehandle:
        lines = [line for line in lines if not line.startswith('#')]
        lines = [line for line in lines if line.strip() != '']
        filehandle.writelines(lines)  

def get_add_lists():
    addlists = []
    try:
        r = request('GET', my_list)
        addlists = r.text.split('\n')
    except:
        if os.path.exists(local_list):
            with open(local_list, 'r') as f:
                addlists = f.read().split('\n') 
        else: addlists = ad_lists_fallback
    return addlists

def download_hosts(hostsfile):
    ad_lists = get_add_lists()
    if os.path.isfile(hostsfile):
        os.remove(hostsfile)
    for adlist in ad_lists:
        try:
            response = request('GET', adlist)
            with open(hostsfile, 'a+') as f:
                f.write(response.text)
        except:
            print(f'Error downloading {adlist}')
    remove_empty_lines(hostsfile)

if __name__ == '__main__':
    ad_lists = get_add_lists()
    base_dir = os.path.dirname(__file__)
    tmp_dir = base_dir + '/tmp'
    script_dir = tmp_dir + '/META-INF/com/google/android'
    if not os.path.isdir(script_dir):
        os.makedirs(script_dir)
    with open(script_dir + '/update-binary', 'w') as f:
        f.write(update_binary)
    with open(script_dir + '/updater-script', 'w') as f:
        f.write('')
    download_hosts(tmp_dir + '/hosts')
    termux_dwn_fld = '/data/data/com.termux/files/home/storage/downloads'
    if os.path.isdir(termux_dwn_fld):
        make_archive(termux_dwn_fld + '/update-hosts', 'zip', tmp_dir)
    else:
        make_archive('update-hosts', 'zip', tmp_dir)
    rmtree(tmp_dir)
    print('Done.')