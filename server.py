import socket
import datetime

class Request:
    def __init__(self, method, uri, version, text, headers):
        self.method = method
        self.uri = uri
        self.version = version
        self.text = text
        self.headers = {}

class Response:
    def __init__(self, version, code, reason, headers, text):
        self.version = version
        self.code = code
        self.reason = reason
        self.headers = headers
        self.text = text

def logRequest(requestObj, responseObj):
    log = f"Request Received: {requestObj.method} {requestObj.uri}\nResponse Sent: {requestObj.uri} {responseObj.code} {responseObj.reason}\n"
    print(log)
    return responseObj

def staticEndpoint(uri, responseHeaders):
    text = ""
    code = None
    try:
        with open (f"{uri[1:]}", "r") as file:
            text = file.read()
            code = 301
            if uri.split(".")[-1] == "js":
                responseHeaders["Content-Type"] = "text/javascript"
            elif uri.split(".")[-1] == "css":
                responseHeaders["Content-Type"] = "text/css"
    except FileNotFoundError:
        text = "File Not Found, look somewhere else!"
        code = 404
    return (text, code)
    
def homeEndpoint():
    with open("templates/index.html", "r") as file:
        return (file.read(), 200)
    
def aboutEndpoint():
    with open("templates/about.html", "r") as file:
        return (file.read(), 200)

def projectEndpoint():
    with open("templates/projects.html", "r") as file:
        return (file.read(), 200)
    
def experienceEndpoint():
    with open("templates/experience.html", "r") as file:
        return (file.read(), 200)
    
def router(uri, responseHeaders):
    if "." in uri:
        endpointTuple = staticEndpoint(uri, responseHeaders)
    else:
        responseHeaders["Content-Type"] = "text/html"
        if uri == "/":
            endpointTuple = homeEndpoint()
        elif uri == "/about":
            endpointTuple = aboutEndpoint()
        elif uri == "/projects":
            endpointTuple = projectEndpoint()
        elif uri == "/experience":
            endpointTuple = experienceEndpoint()
        elif uri == "/info":
            responseHeaders["Location"] = "/about"
            endpointTuple = ("", 301)
        else:
            endpointTuple = ("File Not Found, look somewhere else!", 404)
    return endpointTuple            

def createResponse(next):
    def middleware(requestObj):
        responseHeaders = {"Server": "Ben's HTTP Server", "Connection": "close", "Cache-Control": "max-age=5", "Date": f"{datetime.datetime.now()}"}
        endpointText, endpointCode = router(requestObj.uri, responseHeaders)
        return next(requestObj, Response(requestObj.version, endpointCode, "OK", responseHeaders, endpointText))
    return middleware


def requestParser(data):
    parsed = data.split("\\r\\n")
    info = parsed.pop(0).split(" ")
    method = info.pop(0).replace("b'", "")
    uri = info.pop(0)
    version = info.pop(0).replace("\r", "")
    headerDict = {}
    for i in range(len(parsed)):
        line = parsed[i].split(" ", 1)
        if len(line) == 2:
            headerDict[line[0].replace(":", "")] = line[1].replace("\r", "")
    request = Request(method, uri, version, "OK", headerDict)
    return request

def responseParser(responseObj):
    headerContent = ""
    for key, value in responseObj.headers.items():
        headerContent += f"{key}: {value}\n"
    responseString = f"{responseObj.version} {responseObj.code} {responseObj.reason}\n{headerContent}\n{responseObj.text}"
    return responseString

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(("127.0.0.1", 8000))
    s.listen()
    print("listening on port 8000")

    while True:
        connection, addr = s.accept()
        with connection:
            data = connection.recv(8192)
            if not data:
                connection.close()
                continue

            #TODO: parse the request, send through middleware and encode the response
            request = requestParser(str(data))
            middleware_chain = createResponse(logRequest)
            response = middleware_chain(request)
            res = responseParser(response)

            connection.send(bytes(res, "UTF-8"))




