from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json
from tld import get_tld
import requests
import webbrowser
import dns.resolver


class Message:
    thread = ""
    sender = ""
    link  = ""

    def validSender(): # If has these extensions
        accepts = ['com', 'org','net', 'gov', 'edu']
        for a in accepts:
            if a in sender:
                return true

        return false


class Site:
    def __init__(self):
        self.messages = []

    sender = ""
    domainName = ""
    messages = [Message()]

    def getSender(self):
        return self.sender

    def getDomain(self):
        return self.domain

    def addMessage(self, mail):
        self.messages.append(mail)

    def getString(self):
        fin = ""
        fin += self.sender + " " + self.domainName + " " + str(len(self.messages))
#        for a in self.messages:
#            fin += "\n" + a.link
        return fin

    def getMessageSize(self):
        return len(self.messages)

    def getLink(self):
        return self.messages[0].link


# com , org , us , edu , gov , net ,

def get_records(domain):
    """
    Get all the records associated to domain parameter.
    :param domain:
    :return:
    """
    ids = [ 'A','NS','MD','MF','CNAME','SOA','MB','MG', 'MR','MX','AAAA']

    for a in ids:
        try:
            answers = dns.resolver.query(domain, a)
            for rdata in answers:
                print(a, ':', rdata.to_text())
                return a

        except Exception as e:
            print(e)  # or pass
    return "NA"


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']


def checkDNS(url):
    b = open("valid.txt", "a") # For the shorter valid types
    c = open("invalid.txt", "a") # For the shorter invalid types
    ans = get_records(url)
    if (ans == "NA"):
        c.write(url)
    else:
        b.write(url)
    b.close()
    c.close()


def validURL(url):
    try:
        response = requests.get(url,timeout=.5)
        return True
    except requests.ConnectionError as exception:
        return False
    except :
        return False


def cleanUrl(url):
    newUrl = url.strip()
    if not("mailto" in url): # It is email back
        return newUrl
    else: # It is an actual URL that needs to be cleaned up
        url = newUrl
        newUrl = url.replace("<","").replace(">","").trim()
        return newUrl

def cleanDomain(url):
    newUrl = url.replace("<","").replace(">","").replace(",","").strip()
    startingIndex = 0
    if ("mailto" in newUrl):
        return url
    elif ("https" in newUrl):
        newUrl = newUrl.replace("https://","")
        startingIndex = newUrl.index("/")
        return "https://" + (newUrl[0:startingIndex]).strip()
    elif ("http" in newUrl):
        newUrl = newUrl.replace("http://","")
        startingIndex = newUrl.index("/")
        return "http://" + (newUrl[0:startingIndex]).strip()



def cleanGmail():
    basePath = "User/Gmail/"
    if not os.path.exists(basePath):
        os.mkdir(basePath)
        print("Making the folder. Make sure to put credentials of Gmail account in the " + basePath + " location")
        return "Path did not exist"
    os.chdir(basePath)
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)


    everythingFile = open("Everything.txt", "w")
    # Call the Gmail API
    megaThreadList = [] # All threads/ Emails
    sitesList = [] # List of all sites
    siteNames = [] # Names of sites for easy search
    noReply = [] # Thread of Noreply emails
    moreThreads = True
    threadsList = service.users().threads().list(userId='me',includeSpamTrash=True,prettyPrint=True).execute()
    nextPageToken = threadsList['nextPageToken']
    for thread1 in threadsList['threads']:
        megaThreadList.append(thread1['id'])

    threadPageCounter = 0
    pageLimit = 10
    while moreThreads:
        threadsList = service.users().threads().list(userId='me',includeSpamTrash=True,prettyPrint=True,pageToken=nextPageToken).execute()
        for thread1 in threadsList['threads']:
            megaThreadList.append(thread1['id'])
        if 'nextPageToken' in threadsList:
            nextPageToken = threadsList['nextPageToken']
            if threadPageCounter >= pageLimit: # Cut off after reaching pageLimit
                moreThreads = False
            threadPageCounter += 1
#            print(nextPageToken)
        else:
            moreThreads = False
#    print(threadPageCounter)
    for ids in megaThreadList:
        metaMessage = service.users().threads().get(userId='me',id=ids,format="metadata").execute()
        payloads = (metaMessage['messages'][0]['payload'])
        payloadHeaders = payloads['headers']
        # Name = List-Unsubscribe
        currentEmail = ""
        currentMessage = Message()
        currentMessage.thread = ids
        unsubscribeLink = "" # The unsubscriber link
        for headers in payloadHeaders:
            if(headers['name'] == 'From'):
                temp = headers['value']
                index = -1
                if "<" in temp:
                    index = temp.index("<")
                if (index < 0):
                    currentEmail = temp

                currentEmail = temp[index + 1:-1]
                currentMessage.sender = currentEmail
                if "noreply" in currentEmail or "no-reply" in currentEmail:
                    noReply.append(ids)

            if(headers['name'] == 'List-Unsubscribe'):
                temp = headers['value']
                index = 0
                if "<" in temp:
                    index = temp.index("<")
                currentUnsubscribeLink = temp[index+1:-1]
                unsubscribeLink = currentUnsubscribeLink
                currentMessage.link = currentUnsubscribeLink

        everythingFile.write(currentMessage.sender + "  "+ currentMessage.link + "\n")

        cleanDomainLink = unsubscribeLink
        if "," in unsubscribeLink:
            split = unsubscribeLink.split(",")
            cleanDomainLink = cleanDomain(split[1])
            currentMessage.link = cleanDomainLink
        else:
            cleanDomainLink = cleanDomain(unsubscribeLink)


        if not(cleanDomainLink is None or "mailto" in cleanDomainLink):
            if(validURL(cleanDomainLink)):
                if cleanDomainLink in siteNames: # Already exist
                    currentIndex = siteNames.index(cleanDomainLink)
                    sitesList[currentIndex].addMessage(currentMessage)
                else: # Create new Site
                    currentSite = Site()
                    siteNames.append(cleanDomainLink)
                    currentSite.domainName = cleanDomainLink
                    currentSite.addMessage(currentMessage)
                    currentSite.sender = currentMessage.sender
                    sitesList.append(currentSite)
    everythingFile.flush()
    everythingFile.close()
    siteInformation = open("SitesFile.txt","w") #Information
    unsubLink = open("unsubscribeLinks.txt", "w") # Unsubscribe Links
    ignoreFile = open("ignored.txt","w")
    # If their is one do a get and post request real quick
    for s in sitesList:
        if s.getMessageSize() == 1:
            print("Would you like to delete them messages?")
            ignoreFile.write(s.getSender() + "/n")
            print("Ignoring " + s.getSender())
        else:
            siteInformation.write(s.getString() + "\n")
            unsubLink.write(s.getLink() + "\n")
    siteInformation.close()
    ignoreFile.close()
    unsubLink.close()
    issuesFile = open("issues.txt","w")
    keeping = [] # The ones we are keeping
#    oneTimeResponse = "yes"
#    noReplyResponse = "yes"
    oneTimeResponse = input("Would you like to delete one time messages (yes/no)? ")
    noReplyResponse = input("Would you like to delete noreply messages (yes/no)? ")
    oneTime = oneTimeResponse.lower().strip() == "yes"
    noReplies = noReplyResponse.lower().strip() == "yes"
    counter = 0
    newSet = []
    if (noReplies):
        for nrthread in noReply:
            try:
                service.users().messages().trash(userId='me',id=nrthread).execute() #trashing thread
            except:
                print("That was an issue with " + nrthread)

    for s in sitesList:
        try:
            if s.getMessageSize() == 1 and oneTime:
                service.users().messages().trash(userId='me', id = s.messages.thread).execute()
            if s.getMessageSize() > 1:
                print(str(counter) + ". " + s.getString())
                newSet.append(s)
                counter += 1
        except:
            issuesFile.write(s.getString())
            print("that message does not exist")

    deletingRecords = open("deleting.txt", "w")
    keeping = input("enter in the number seperated by a , of the ones you want to keep: ")
    issuesFile.write("\nhere is the split\n\n")
    spliting = keeping.split(",")
#    spliting = []
    counter = 0
    for splits in spliting:
        if not (counter == splits):
            deletingRecords.write(newSet[counter].sender + "\n")
            for mes in newSet[counter].messages:
                try:
                    service.users().messages().trash(userId='me',id=mes.thread).execute()
                except:
                    issuesFile.write(mes.getString())
        counter += 1
    # Deleting the messages here
    deletingRecords.flush()
    deletingRecords.close()
    issuesFile.close()

    # Opening up all the unsubscribes
    readUnsubLinks = open("webSiteFile.txt","r")
    lines = readUnsubLinks.readlines()
    browserCount = 0
    maxBrowsers = 5
    for line in lines:
        if browserCount >= maxBrowsers: # Max tabs to open
            webbrowser.open(line)
        browserCount += 1
    readUnsubLinks.close()
    os.chdir("../../")
    return "All done cleaning"
