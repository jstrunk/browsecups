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

#user in the admin group who can use the local CUPS web interface
username="administrator"
password="xxxx"

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
    try:
        cups.setServer(sys.argv[1])
    except IndexError:
        print """Usage: {} <hostname>""".format(sys.argv[0])
        sys.exit(1)
    
    rc = cups.Connection()
    
    printers = rc.getPrinters()
    
    cups.setServer("/private/var/run/cupsd")
    cups.setUser(username)
    cups.setPasswordCB(lambda x: password)
    lc = cups.Connection()
    
    for p in printers.keys():
        ppd = findppd(lc, printers[p])
        if ppd is not None:
            lc.addPrinter(p, device=printers[p]['printer-uri-supported'], location=printers[p]['printer-location'], info=printers[p]['printer-info'], ppdname=ppd)
        else:
            lc.addPrinter(p, device=printers[p]['printer-uri-supported'], location=printers[p]['printer-location'], info=printers[p]['printer-info'])
        lc.setPrinterShared(p, False)
        lc.enablePrinter(p)
        lc.acceptJobs(p)
    
