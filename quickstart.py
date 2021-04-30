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
#        print("URL is valid and exists on the internet")
    except requests.ConnectionError as exception:
        return False
    except :
        return False
#        print("URL does not exist on Internet")


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
    startInd = 0
    if ("mailto" in newUrl):
        return url
    elif ("https" in newUrl):
        newUrl = newUrl.replace("https://","")
        startInd = newUrl.index("/")
        return "https://" + (newUrl[0:startInd]).strip()
    elif ("http" in newUrl):
        newUrl = newUrl.replace("http://","")
        startInd = newUrl.index("/")
        return "http://" + (newUrl[0:startInd]).strip()
        


def main():
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
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    f = open("Everything.txt", "w")
    # Call the Gmail API
    megaThreadList = [] # All threads/ Emails
    sitesList = [] # List of all sites
    siteNames = [] # Names of sites for easy search
    ar = [] # Email From
    arSmall = [] # Unique email from
    noReply = [] # Thread of Noreply emails
    moreThreads = True
    threadsList = service.users().threads().list(userId='me',includeSpamTrash=True,prettyPrint=True).execute()
    nextPageToken = threadsList['nextPageToken']
    for thread1 in threadsList['threads']:
        megaThreadList.append(thread1['id'])

    ix = 0
    while moreThreads:
        threadsList = service.users().threads().list(userId='me',includeSpamTrash=True,prettyPrint=True,pageToken=nextPageToken).execute()
        for thread1 in threadsList['threads']:
            megaThreadList.append(thread1['id'])
        if 'nextPageToken' in threadsList:
            nextPageToken = threadsList['nextPageToken']
            if ix >= 10000: # Cut off after second page
                moreThreads = False
            ix += 1
            print(nextPageToken)
        else:
            moreThreads = False
    print(ix)
    for ids in megaThreadList:
        metaMessage = service.users().threads().get(userId='me',id=ids,format="metadata").execute()
#        fullMessage = service.users().threads().get(userId='me',id=ids,format="full").execute()
#        print(metaMessage)
        payloads = (metaMessage['messages'][0]['payload'])
        head = payloads['headers']
        # Name = List-Unsubscribe
        curEmail = ""
        curMess = Message()
        curMess.thread = ids
        unsub = "" # The unsubscriber link
        for pay in head:
            if(pay['name'] == 'From'):
                temp = pay['value']
                ind = -1
                if "<" in temp:
                    ind = temp.index("<")
                if (ind < 0):
                    curEmail = temp

                curEmail = temp[ind+1:-1]
                curMess.sender = curEmail
                ar.append(curEmail)
                if "noreply" in curEmail or "no-reply" in curEmail:
                    noReply.append(ids)

            if(pay['name'] == 'List-Unsubscribe'):
                temp = pay['value']
                ind = 0
                if "<" in temp:
                    ind = temp.index("<")
                curLink = temp[ind+1:-1]
                unsub = curLink
                curMess.link = curLink

        f.write(curMess.sender + "  "+ curMess.link + "\n")

        cleanDom = unsub
        if "," in unsub:
            split = unsub.split(",")
            cleanDom = cleanDomain(split[1])
            curMess.link = cleanDom
        else:
            cleanDom = cleanDomain(unsub)


        if not(cleanDom is None or "mailto" in cleanDom):
            if(validURL(cleanDom)):
                if cleanDom in siteNames: # Already exist
                    curIndex = siteNames.index(cleanDom)
                    sitesList[curIndex].addMessage(curMess)
                else: # Create new Site
                    curSite = Site()
                    siteNames.append(cleanDom)
                    curSite.domainName = cleanDom
                    curSite.addMessage(curMess)
                    curSite.sender = curMess.sender
                    sitesList.append(curSite)
    f.flush()
    f.close()
    fsd = open("SitesFile.txt","w")
    fs = open("webSiteFile.txt", "w")
    fsa = open("ignored.txt","w")
    # If their is one do a get and post request real quick
    for s in sitesList:
        if s.getMessageSize() == 1:
            print("Would you like to delete them messages?")
            fsa.write(s.getSender() + "/n")
            print("Ignoring " + s.getSender())
        else:
            fsd.write(s.getString() + "\n")
            fs.write(s.getLink() + "\n")
    fsd.close()
    fsa.close()
    fs.close()
#    print(noReply)
    fq = open("issues.txt","w")
    keeping = [] # The ones we are keeping
    oneTimeResponse = "yes"
    noReplyResponse = "yes"
#    oneTimeResponse = input("Would you like to delete one time messages (yes/no)? ")
#    noReplyResponse = input("Would you like to delete noreply messages (yes/no)? ")
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
            fq.write(s.getString())
            print("that message does not exist")
        
    fsb = open("deleting.txt", "w")
#    keeping = input("enter in the number seperated by a , of the ones you want to keep: ")
    fq.write("\nhere is the split\n\n")
#    spliting = keeping.split(",")
    spliting = []
    counter = 0
    for splits in spliting:
        if not (counter == splits):
            fsb.write(newSet[counter].sender + "\n")
            for mes in newSet[counter].messages:
                try:
                    service.users().messages().trash(userId='me',id=mes.thread).execute()
                except:
                    fq.write(mes.getString())
#                    print("That thread does not exist")
        counter += 1
    # Deleting the messages here
    fsb.flush()
    fsb.close()
    fq.close()

    # Opening up all the unsubscribes
    fr = open("webSiteFile.txt","r")
    lx = fr.readlines()
    ci = 0
    for lx1 in lx:
        if ci >=5: # only opening 5 browsers at a time
            webbrowser.open(lx1)
        ci += 1
    fr.close()
    
if __name__ == '__main__':
    main()
