#!/usr/bin/python

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
    
