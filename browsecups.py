#!/usr/bin/python

"""
Copyright (C) 2012  The University of Texas at Austin.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Written by: Jeff Strunk, Department of Mathematics,
The University of Texas at Austin 78712.    jstrunk@math.utexas.edu
"""

import cups
import sys
from Foundation import CFPreferencesCopyAppValue

BUNDLE_ID = 'edu.utexas.ma.browsecups'


def findppd(c, printer):
    """Find a matching PPD using the longest matching substring from model.
    This is reasonable because the model names on the client and server may vary slightly, and thereis some stange non-matching behavior. E.g. 'Kyocera FS-4020DN (KPDL)' does not return 'Kyocera FS-4020DN (KPDL)' in getPPDs(), but 'Kyocera FS-4020DN' does."""
    model = printer['printer-make-and-model']
    while len(model) >= 9:
        """This step is slow. I use minimum of 9 characters to match HP deskjet. A smaller number may find more valid matches, but it will take longer. We don't use any drivers with less than 9 characters."""
        try:
            ppds = c.getPPDs(ppd_make_and_model=model)
        except cups.IPPError:
            model = model.rstrip(model[-1])
        else:
            if len(ppds) == 1:
                return ppds.keys()[0]
            else:
                """check to see if any models match the original exactly"""
                for ppd,meta in ppds.iteritems():
                    if meta['ppd-make-and-model'] == printer['printer-make-and-model']:
                        return ppd
                else:
                    return None
    return None

if __name__ == '__main__':
    if len(sys.argv) == 2:
        server = sys.argv[1]
        interactive = True
    elif ((CFPreferencesCopyAppValue('server', BUNDLE_ID) is None) or
       (CFPreferencesCopyAppValue('username', BUNDLE_ID) is None) or
       (CFPreferencesCopyAppValue('password', BUNDLE_ID) is None)):
        print """Usage: {program} hostname

To run in non-interactive mode, {program} requires the following preferences to be defined in the {domain} domain:
    server - The hostname of your CUPS server.
    username - A user on the local machine who can use the CUPS web administration interface.
    password - That user's password

The easiest way to create this is to run the following commands as root:
    defaults write {domain} server hostname
    defaults write {domain} username administrator
    defaults write {domain} password xxxx

This will create /var/root/Library/Preferences/{domain}.plist
        """.format(program=sys.argv[0], domain=BUNDLE_ID)
        sys.exit(1)
    else:
        server = CFPreferencesCopyAppValue('server', BUNDLE_ID)
        username = CFPreferencesCopyAppValue('username', BUNDLE_ID)
        password = CFPreferencesCopyAppValue('password', BUNDLE_ID)
        interactive = False
       
    cups.setServer(server)
    
    try:
        rc = cups.Connection()
    except RuntimeError, e:
        print e
        sys.exit(2)
    try:
        printers = rc.getPrinters()
    except cups.IPPError, (code, msg):
        print "Error retrieving printer list: {}".format(msg)
        sys.exit(3)
    
    cups.setServer("/private/var/run/cupsd")
    if not interactive:
        cups.setUser(username)
        cups.setPasswordCB(lambda x: password)

    lc = cups.Connection()
    
    for p in printers.keys():
        try:
            ppd = findppd(lc, printers[p])
            if ppd is not None:
                lc.addPrinter(p, device=printers[p]['printer-uri-supported'], location=printers[p]['printer-location'], info=printers[p]['printer-info'], ppdname=ppd)
            else:
                lc.addPrinter(p, device=printers[p]['printer-uri-supported'], location=printers[p]['printer-location'], info=printers[p]['printer-info'])
            lc.setPrinterShared(p, False)
            lc.enablePrinter(p)
            lc.acceptJobs(p)
        except cups.IPPError, (code, msg):
            print "Could not add/modify printer {}: {}".format(p, msg)
            sys.exit(code)
    
