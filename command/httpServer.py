import BaseHTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer
import urlparse
import cgi
import json
#import  testGrid
from testGrid import testGridController
from parseCommandLine import argHttp
from collections import OrderedDict

SERVER_IP = '192.168.0.8'
testGrid = testGridController()



def deserialiseur_perso(obj_dict):
    if "__class__" in obj_dict:
        if obj_dict["__class__"] == "argHttp":
            obj = argHttp(obj_dict["value"], obj_dict["root"])
            if "root" in obj_dict:
                obj.rootPass = obj_dict["root"]
            return obj
    return None



class testGridHandler(BaseHTTPRequestHandler):
    

    def do_GET(self):
        parsed_path = urlparse.urlparse(self.path)
        message_parts = [
                'CLIENT VALUES:',
                'client_address=%s (%s)' % (self.client_address,
                                            self.address_string()),
                'command=%s' % self.command,
                'path=%s' % self.path,
                'real path=%s' % parsed_path.path,
                'query=%s' % parsed_path.query,
                'fragment=%s' % parsed_path.fragment,
                'request_version=%s' % self.request_version,
                '',
                'SERVER VALUES:',
                'server_version=%s' % self.server_version,
                'sys_version=%s' % self.sys_version,
                'protocol_version=%s' % self.protocol_version,
                '',
                'HEADERS RECEIVED:',
                ]
        for name, value in sorted(self.headers.items()):
            message_parts.append('%s=%s' % (name, value.rstrip()))
        message_parts.append('')
        message = '\r\n'.join(message_parts)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(message)
        print "END"
        return



    def do_POST(self):
        httpArg = argHttp()
        form = cgi.FieldStorage(
            fp=self.rfile, 
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })
        self.send_response(200)
        self.end_headers()
        self.wfile.write('Client: %s\n' % str(self.client_address))
        httpArg = json.loads(form.value, object_hook=deserialiseur_perso)
        if str(self.client_address[0]) == SERVER_IP:
            httpArg.isAdmin = True
        result = testGrid.manageArg(httpArg)
        self.wfile.write(result + '\n')
        return

        """for field in form.keys():
            field_item = form[field]
            if field == 'admin':
        
                    print "client adress %s\n" % self.client_address[0]
                    result = "you must be admin to perform this operation"
                    self.wfile.write(result + '\n')
                else:
                    self.wfile.write('\t%s=%s\n' % (field, form[field].value))
                    httpArg.commandLine = form[field].value
                    httpArg.isAdmin = True

                    result = testGrid.manageArg(to_arg(form[field].value))
                    print "RESULT %s " % result
                    self.wfile.write(result + '\n')
            if field == 'command':
                if len(form[field]) > 1:
                    print "to many command"
                else:
                    httpArg.commandLine = form[field].value
                self.wfile.write('\t%s=%s\n' % (field, form[field].value))
                
                print "RESULT %s " % result
                
                
        return"""





if __name__ == '__main__':
    server = HTTPServer((SERVER_IP, 8080), testGridHandler)
    print 'Starting server, use <Ctrl-C> to stop'
    server.serve_forever()



    """s1=SingleTone(testGridController)
    s2=SingleTone(testGridController)
    if(id(s1)==id(s2)):
        print "Same"
    else:
        print "Different"""
