import os
from datetime import date
from shutil import make_archive, rmtree
import io
import sys
import time
from urllib.parse import urlparse
from urllib.request import urlopen

if not sys.version_info >= (3, 0):
    sys.exit("Python 2 is not supported. Exiting...")

DT = time.strftime("%b %d, %Y %H:%M:%S %Z")
DTB = time.strftime("%b %d, %Y %H.%M.%S")

PATH = os.path.dirname(os.path.abspath(__file__))
SOURCES_FILE = os.path.join(PATH, "sources")
BLACKLIST_FILE = os.path.join(PATH, "blacklist")
WHITELIST_FILE = os.path.join(PATH, "whitelist")
CUSTOM_FILE = os.path.join(PATH, "custom")
TMP_DIR = os.path.join(PATH, 'tmp')
NEW_HOSTS_FILE = os.path.join(TMP_DIR, "hosts")
SCRIPT_DIR = os.path.join(TMP_DIR, 'META-INF','com','google','android')
TERMUS_FLD = '/data/data/com.termux/files/home/storage/downloads'

IP_LIST = ["127.0.0.1", "0.0.0.0"]
SKIP_LIST = ["local", "localhost", "localhost.localdomain"]
PREFIX = "0.0.0.0"

tab = " "*4

UPDATE_BINARY_FILE = f'''#!/sbin/sh
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

class unifiedHosts():
    def __init__(self):
        self.sources = []
        self.blacklist = set()
        self.whitelist = set()
        self.customlist = set()
        self.customlist_dom = set()
        self.sw_set = set()
        self.ew_set = set()
        self.in_set = set()
        self.eq_set = set()
        self.download_set = set()
        self.new_hosts_set = set()
        self.whitelist_set = set()

        self.processLists()
        self.downloadHosts()
        self.makeHosts()

    def processLists(self):
        msg("Processing:\n")
        try:
            msg(tab + "Sources.....")
            if os.path.exists(SOURCES_FILE):
                with open(SOURCES_FILE, "r") as f:
                    seen = set()
                    for line in f:
                        line = line.strip()
                        if (line and not line.startswith("#") and
                                line not in seen):
                            self.sources.append(line)
                            seen.add(line)
                self.source_c = len(self.sources)
                if self.source_c == 0:
                    msg("failed. No source URLs were found.", 0)
                else:
                    msg("ok (" + str(self.source_c) + " urls)\n")
                    url_len = 0
                    for line in self.sources:
                        if len(line) > url_len:
                            url_len = len(line)
                            self.col_max = url_len
            else:
                msg("failed. ('sources' file is missing.)", 0)

            msg(tab + "Custom list...")
            if os.path.exists(CUSTOM_FILE):
                with open(CUSTOM_FILE, "r") as f:
                    for line in f:
                        line = line.strip().lower()
                        if line and not line.startswith("#"):
                            try:
                                line_dom = line.split()[1]
                            except:
                                line_dom = line
                            self.customlist_dom.add(line_dom)
                            self.customlist.add(line)
                self.customlist_c = len(self.customlist)
                msg("ok (" + str(self.customlist_c) + " entries)\n")
            else:
                msg("failed. ('custom' file is missing.)\n")

            msg(tab + "Blacklist...")
            if os.path.exists(BLACKLIST_FILE):
                with open(BLACKLIST_FILE, "r") as f:
                    ignored = set()
                    for line in f:
                        line = line.strip().lower()
                        if (line and not line.startswith("#") and
                                line not in self.customlist_dom):
                            self.blacklist.add(line)
                        elif line in self.customlist_dom:
                            ignored.add(line)
                ignored_c = len(ignored)
                if ignored_c > 0:
                    im = ", " + str(ignored_c) + " ignored"
                else:
                    im = ""
                self.blacklist_c = len(self.blacklist)
                msg("ok (" + str(self.blacklist_c) + " entries" + im + ")\n")
            else:
                msg("failed. ('blacklist' file is missing.)\n")

            msg(tab + "Whitelist...")
            if os.path.exists(WHITELIST_FILE):
                with open(WHITELIST_FILE, "r") as f:
                    for line in f:
                        line = line.strip().lower()
                        if (line and not line.startswith("#") and
                                line not in self.customlist_dom):
                            self.whitelist.add(line)
                        elif line in self.customlist_dom:
                            ignored.add(line)
                ignored_c = len(ignored)
                if ignored_c > 0:
                    im = ", " + str(ignored_c) + " ignored"
                else:
                    im = ""
                self.whitelist_c = len(self.whitelist)
                for line in self.whitelist:
                    if line.startswith("*") and line.endswith("*"):
                        line = line.replace("*", "").strip()
                        self.in_set.add(line)
                    elif line.endswith("*"):
                        line = line.replace("*", "").strip()
                        self.sw_set.add(line)
                    elif line.startswith("*"):
                        line = line.replace("*", "").strip()
                        self.ew_set.add(line)
                    elif line:
                        self.eq_set.add(line)
                msg("ok (" + str(self.whitelist_c) + " entries" + im + ")\n")
            else:
                msg("failed. ('whitelist' file is missing.)\n")

        except Exception as e:
            msg("failed. (" + str(e) + ")", 0)

    def urlStr(self, url, url_c, prog=""):
        spc = 1
        prog_spc = 25
        try:
            offset = self.col_max
            term_size = int(os.get_terminal_size().columns)
            a_spc = term_size - prog_spc - len(tab)
            if a_spc > self.col_max:
                a_spc = self.col_max

            if len(url) > a_spc:
                dots = "..."
                offset = a_spc - len(dots)
            else:
                dots = ""
                spc = a_spc - len(url) + spc
            urlStr = tab + url[:offset] + dots + " "*spc + "| " + prog
            urlStr = urlStr + " "*(term_size - len(urlStr) - len(tab)) + "\r"
        except:
            urlStr = tab + str(url_c) + " "*(3 - len(str(url_c)))
            urlStr = urlStr + " "*(5-len(urlStr)) + "| " + prog + tab + "\r"
        return urlStr

    def downloadHosts(self):
        msg("\nDownloading from following source(s):\n")
        clear_prog = 20
        url_c = 0
        err_c = 0
        for url in self.sources:
            self.domain_c = set()
            data = []
            byte_size = 1024
            bytes_down = 0
            url_c += 1
            msg(self.urlStr(url, url_c))
            try:
                content = urlopen(url, timeout=60)
                try:
                    length = float(content.info()["Content-Length"])
                    size = "{0:,.0f} KB".format(length/1024)
                except:
                    size = "??? KB"

                while True:
                    buffer = content.read(byte_size)
                    bytes_down += len(buffer)
                    data.append(buffer)
                    if not len(buffer):
                        break
                    prog = "{0:,.0f} KB".format(bytes_down/1024) + "/" + size
                    msg(self.urlStr(url, url_c, prog))

                download = io.BytesIO(b"".join(data))
                msg(self.urlStr(url, url_c, " "*clear_prog))
                msg(self.urlStr(url, url_c, "Processing..."))
                self.processDownload(download)
                prog = str(len(self.domain_c)) + " domains"
                msg(self.urlStr(url, url_c, prog))
            except Exception as e:
                err_c += 1
                prog = "Failed (" + str(e) + ")"
                msg(self.urlStr(url, url_c, prog))
            msg("\n")
        if err_c == self.source_c:
            msg("Download failed.", 0)

    def processDownload(self, download):
        for line in download:
            try:
                line = line.decode("utf-8").lower()
                if len(line.split()) > 1:
                    line_ip = line.split()[0]
                    line_url = line.split()[1]
                    if line_ip in IP_LIST and line_url not in IP_LIST:
                        line = urlparse("//" + line_url).netloc
                        line = line.encode("idna").decode("utf-8")
                        self.domain_c.add(line)
                        self.download_set.add(line)
            except:
                pass

    def makeHosts(self):
        msg("\nGenerating new adBlock hosts file...")
        try:
            for line in self.download_set:
                if (any(w in line for w in self.in_set) or
                    any(line.startswith(w) for w in self.sw_set) or
                    any(line.endswith(w) for w in self.ew_set) or
                        line in self.eq_set):
                    self.whitelist_set.add(line)
                if (line not in self.blacklist and
                        line not in self.whitelist_set and
                        line not in self.customlist_dom and
                        line not in SKIP_LIST):
                    self.new_hosts_set.add(line)

            nhs_c = str(len(self.new_hosts_set))
            wls_c = str(len(self.whitelist_set))
            bls_c = str(self.blacklist_c)
            cst_c = str(self.customlist_c)
            with open(NEW_HOSTS_FILE, "w+") as f:
                f.write("\n# Last updated: " + DT + "\n")
                f.write("\n# Custom entries (" + cst_c + "):\n")
                for line in sorted(self.customlist):
                    f.write(line + "\n")
                f.write("\n# Blacklisted domains (" + bls_c + "):\n")
                for line in sorted(self.blacklist):
                    f.write(PREFIX + " " + line + "\n")
                f.write("\n# Whitelisted domains (" + wls_c + "):\n")
                for line in sorted(self.whitelist_set):
                    f.write("# " + line + "\n")
                f.write("\n# Blocked domains (" + nhs_c + "):\n")
                for line in sorted(self.new_hosts_set):
                    f.write(PREFIX + " " + line + "\n")
                f.write("## End adBlock hosts file ##\n")
            msg("done.\n" + tab + "Saved to: " + NEW_HOSTS_FILE + "\n\n")
            msg(tab + "Blocked " + nhs_c + " unique domains.\n"
                + tab + "Added " + cst_c + " custom entries.\n"
                + tab + "Blacklisted " + bls_c + " domains.\n"
                + tab + "Whitelisted " + wls_c + " domains.\n")
        except Exception as e:
            msg("failed.\n\t" + str(e), 0)

class msg():
    def __init__(self, msg, code=None):
        sys.stdout.write(msg)
        sys.stdout.flush()
        if code == 0:
            sys.exit("\nExiting...")

if __name__ == '__main__':
    if not os.path.isdir(SCRIPT_DIR):
        os.makedirs(SCRIPT_DIR)
    with open(SCRIPT_DIR + '/update-binary', 'w') as f:
        f.write(UPDATE_BINARY_FILE)
    with open(SCRIPT_DIR + '/updater-script', 'w') as f:
        f.write('')
    unifiedHosts()
    if os.path.isdir(TERMUS_FLD):
        make_archive(TERMUS_FLD + '/update-hosts', 'zip', TMP_DIR)
    else:
        make_archive('update-hosts', 'zip', TMP_DIR)
    rmtree(TMP_DIR)
    msg("\nProcess complete.\n")