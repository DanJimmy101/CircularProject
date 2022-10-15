from xmlrpc.client import Boolean
from fastapi import Body, Depends, FastAPI, Response, Request, File, UploadFile, status, Form
from typing import Optional, Union
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
# from jmespath import search
from pydantic import BaseSettings, BaseModel
from fastapi_login import LoginManager
from fastapi_login.exceptions import InvalidCredentialsException
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import os, time
import json
import math

from Pdf2Txt import onePdfToTxtWithCategories
from utility import docfile, wordfile, wordlocfile
from runner import Search
from tfidfRecommender import getRecommendations
from tinyDB import tiny_db_search_data
from doclistRead import doclistData

class NotAuthenticatedException(Exception):
    pass

def not_auth_exc_handler(request, exc):
    return RedirectResponse(url='/login', status_code=status.HTTP_303_SEE_OTHER)

class Settings(BaseSettings):
    secret: str  # automatically taken from environment variable

class user_history(BaseModel):
    user_search_history: str
    user_click_history: str
    user_min_value: float
    user_max_value: float

class delete_user_history(BaseModel):
    user_click_history: str

DEFAULT_SETTINGS = Settings(_env_file=".env")

templates = Jinja2Templates(directory="views")

TOKEN_URL = "/auth/token"

app = FastAPI()

manager = LoginManager(
    DEFAULT_SETTINGS.secret,
    TOKEN_URL,
    use_cookie=True,
    use_header=False
)
manager.cookie_name = "access_token"
manager.not_authenticated_exception = NotAuthenticatedException

app.add_exception_handler(NotAuthenticatedException, not_auth_exc_handler)

app.mount("/static", StaticFiles(directory="./views"), name="static")
app.mount("/doc", StaticFiles(directory="./incoming_data"), name="doc")
app.mount("/massUpload", StaticFiles(directory="./massUpload"), name="massUpload")

DB = {'users':
      {'admin@admin.com':
       {
           'email': "admin@admin.com",
           'password': "admin",
           'id': "ca58831c-55c9-4e12-b84e-8a708a997f3e"
       },
       }
      }

# user history of the viewed docs
doc_history_count = 5

# user searched keywords
search_history_count = 5

@manager.user_loader
def get_user(email: str):
    return DB["users"].get(email)

def save_file(filename, data):
    with open(filename, 'wb') as f:
        f.write(data)
        print(filename)
        # use "filename" to get the path of the pdf to scrape

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("./public/home.html", {"request": request})

@app.post(TOKEN_URL)
def login(response: Response, data: OAuth2PasswordRequestForm = Depends()):
    
    email = data.username
    passwordIncoming = data.password

    user = get_user(email)
    userp = user['password']

    if not user:
        raise InvalidCredentialsException  # you can also use your own HTTPException
    elif passwordIncoming != userp:
        raise InvalidCredentialsException

    access_token = manager.create_access_token(
        data=dict(sub=email)
    )

    # sometimes access_token comes with utf-8 encoded
    try:
        access_token.decode('utf-8')
        access_token = access_token.decode('utf-8')
    except:
        print("string is not UTF-8")

    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=access_token, max_age="750")

    return response


@app.get("/search", response_class=HTMLResponse)
def index(request: Request):
    params = dict(request.query_params)
    print(params["search_year"])
    if "categorytexts" in params:
        categorytexts = params["categorytexts"]
        if categorytexts == "":
            categorytexts = None
    else:
        categorytexts = None
    if "search_year" in params:
        search_year = params["search_year"]
    else:
        search_year = None
    if "search_keyword" in params:
        search_keyword = params["search_keyword"]
    else:
        search_keyword = ""
    if "match_check" in params:
        match_check = params["match_check"]
    else:
        match_check = False
    if "max_per_one_page" in params:
        max_per_one_page = int(params["max_per_one_page"])
    else:
        max_per_one_page = 10
    if "page_number" in params:
        page_number = int(params["page_number"])
    else:
        page_number = 1
    if search_keyword.startswith('"') and search_keyword.endswith('"'):
        if search_keyword:
            sp = Search(docfile, wordfile, wordlocfile)
            data_before_to_user = sp.phrasequery(search_keyword, search_year, categorytexts)
            print(data_before_to_user)
            newData = {"results": json.dumps([o.__dict__ for o in data_before_to_user])}
            allData = json.loads(newData["results"])
            allDataLength = len(allData)
            rangeStart = (page_number - 1) * max_per_one_page
            rangeEnd = (page_number * max_per_one_page) if (page_number * max_per_one_page) <= allDataLength else allDataLength
            data_to_user = []
            for k in range(rangeStart,rangeEnd):
                beforeIdChange = json.loads(newData["results"])[k]
                beforeIdChange['displayId'] = json.loads(newData["results"])[k]['id'].rsplit("-",1)[0]
                beforeIdChange['fileSize'] = json.loads(newData["results"])[k]['size']
                beforeIdChange['pdfYear'] = json.loads(newData["results"])[k]['year']
                data_to_user.append(beforeIdChange)
            if categorytexts == None:
                categorytexts = ""
            if search_year == None:
                search_year = ""
            print("matched")
            return templates.TemplateResponse("./public/search.html", {"request": request, "search": search_keyword, "result": data_to_user, "doc_history_count": doc_history_count, "search_history_count": search_history_count, "search_term": search_keyword, "match_value": match_check, "check": "checked", "page_num": page_number, "all_data_length": allDataLength, "max_per_one_page": max_per_one_page, "year": search_year, "tags": categorytexts})
        else:
            return RedirectResponse("/")
    else:
        if search_keyword:
            sp = Search(docfile, wordfile, wordlocfile)
            data_before_to_user = sp.query(search_keyword, search_year, categorytexts)
            newData = {"results": json.dumps([o.__dict__ for o in data_before_to_user])}
            allData = json.loads(newData["results"])
            allDataLength = len(allData)
            rangeStart = (page_number - 1) * max_per_one_page
            rangeEnd = (page_number * max_per_one_page) if (page_number * max_per_one_page) < allDataLength else allDataLength
            data_to_user = []
            for k in range(rangeStart,rangeEnd):
                beforeIdChange = json.loads(newData["results"])[k]
                beforeIdChange['displayId'] = json.loads(newData["results"])[k]['id'].rsplit("-",1)[0]
                beforeIdChange['fileSize'] = json.loads(newData["results"])[k]['size']
                beforeIdChange['pdfYear'] = json.loads(newData["results"])[k]['year']
                data_to_user.append(beforeIdChange)
            if categorytexts == None:
                categorytexts = ""
            if search_year == None:
                search_year = ""
            print("not matched")
            return templates.TemplateResponse("./public/search.html", {"request": request, "search": search_keyword, "result": data_to_user, "doc_history_count": doc_history_count, "search_history_count": search_history_count, "search_term": search_keyword, "match_value": match_check, "check": "", "page_num": page_number, "all_data_length": allDataLength, "max_per_one_page": max_per_one_page, "year": search_year, "tags": categorytexts})
        else:
            return RedirectResponse("/")

@app.get("/advancesearch", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("./public/advanceSearch.html", {"request": request})

@app.get("/advancesearchresult", response_class=HTMLResponse)
def index(request: Request):
    params = dict(request.query_params)
    if "categorytexts" in params:
        categorytexts = params["categorytexts"]
        if categorytexts == "":
            categorytexts = None
    else:
        categorytexts = None
    if "search_year" in params:
        search_year = params["search_year"]
    else:
        search_year = None
    if "search_keyword" in params:
        search_keyword = params["search_keyword"]
    else:
        search_keyword = ""
    if "match_check" in params:
        match_check = params["match_check"]
    else:
        match_check = False
    if "max_per_one_page" in params:
        max_per_one_page = int(params["max_per_one_page"])
    else:
        max_per_one_page = 10
    if "page_number" in params:
        page_number = int(params["page_number"])
    else:
        page_number = 1
    if "all_these_words" in params:
        all_these_words = params["all_these_words"]
    else:
        all_these_words = None
    if "none_of_these_words" in params:
        none_of_these_words = params["none_of_these_words"]
        print(none_of_these_words + "   PFRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR")
    else:
        none_of_these_words = None
    if search_keyword or all_these_words or none_of_these_words:
        sp = Search(docfile, wordfile, wordlocfile)
        data_before_to_user = sp.advancedQuery(search_keyword, all_these_words, none_of_these_words, search_year, categorytexts)
        # print(data_before_to_user)
        newData = {"results": json.dumps([o.__dict__ for o in data_before_to_user])}
        allData = json.loads(newData["results"])
        allDataLength = len(allData)
        rangeStart = (page_number - 1) * max_per_one_page
        rangeEnd = (page_number * max_per_one_page) if (page_number * max_per_one_page) <= allDataLength else allDataLength
        data_to_user = []
        for k in range(rangeStart,rangeEnd):
            beforeIdChange = json.loads(newData["results"])[k]
            beforeIdChange['displayId'] = json.loads(newData["results"])[k]['id'].rsplit("-",1)[0]
            beforeIdChange['fileSize'] = json.loads(newData["results"])[k]['size']
            beforeIdChange['pdfYear'] = json.loads(newData["results"])[k]['year']
            data_to_user.append(beforeIdChange)
        if categorytexts == None:
            categorytexts = ""
        if search_year == None:
            search_year = ""
        print("matched")
        return templates.TemplateResponse("./public/advanceResults.html", {"request": request, "search": search_keyword, "result": data_to_user, "doc_history_count": doc_history_count, "search_history_count": search_history_count, "search_term": search_keyword, "match_value": match_check, "check": "checked", "page_num": page_number, "all_data_length": allDataLength, "max_per_one_page": max_per_one_page, "year": search_year, "tags": categorytexts, "all_these_words": all_these_words, "none_of_these_words": none_of_these_words})
    else:
        return RedirectResponse("/")

@app.get("/data")
def getDataFromEndpoint(request: Request, value: str):
    print(value)
    data = tiny_db_search_data(value)
    print(data)
    return data
    # return {"car","van","bike"}

@app.get("/dashboard")
def getPrivateendpoint(request: Request, user=Depends(manager)):
    return templates.TemplateResponse("./private/dashboard.html", {"request": request, "status_message": ""})

@app.post("/dashboard")
# async def getPrivateendpoint(request: Request, uploadedfile: UploadFile = File(...), categorytexts: Union[str, None] = None, user=Depends(manager)):
async def getPrivateendpoint(request: Request, uploadedfile: UploadFile = File(...), categorytexts: Union[str, None] = Form(None)):
    contents = await uploadedfile.read()
    time_now = str(time.time())
    base = os.path.basename(uploadedfile.filename)
    print(os.path.splitext(base)[0])
    print(categorytexts)
    file_name = './incoming_data/' + os.path.splitext(base)[0] + '-' + time_now + os.path.splitext(base)[1]
    save_file((file_name), contents)
    outputFolder = './ScrapedPDFs/'
    file_name_output = './ScrapedPDFs/'+ os.path.splitext(os.path.basename(file_name))[0] + '.txt'
    onePdfToTxtWithCategories(file_name, file_name_output, str(categorytexts))

    return templates.TemplateResponse("./private/dashboard.html", {"request": request, "status_message": '<div class="alert alert-success d-flex align-items-center alert-dismissible fade show" role="alert"><svg class="bi flex-shrink-0 me-2" width="24" height="24" role="img" aria-label="Success:"><use xlink:href="#check-circle-fill"/></svg><div>File <i>&quot;' + uploadedfile.filename + '&quot;</i> uploaded successfully.<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div></div>'})


@app.get("/login")
def getPrivateendpoint(request: Request):
    return templates.TemplateResponse("./public/login.html", {"request": request})


@app.get("/logout")
def logout(response : Response, user=Depends(manager)):
  response = RedirectResponse("/", status_code= 302)
  response.delete_cookie(key ="access_token")
  return response

@app.post("/recomendations")
def recomended_things(request: Response, user_data: user_history):
    print("------------------------------------------------------")
    # click_data = json.loads(user_data.user_click_history)
    # # print("------------------------------------------------------")
    if(len(user_data.user_click_history) > 0):
        clickedDocuments = user_data.user_click_history.split(',')
        clickedDocuments = [document + '.txt'  for document in clickedDocuments]

        # print("min")
        # print(user_data.user_min_value)
        # print("max")
        # print(user_data.user_max_value)
        
        # use "user_data" to get the click history and the search history of the user
        # print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
        # print(clickedDocuments)
        # print(user_data.user_min_value)
        # print(user_data.user_max_value)
        # print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
        lstRecommendations = getRecommendations(clickedDocuments, user_data.user_min_value, user_data.user_max_value)
        # print(lstRecommendations[0][:lstRecommendations[0].rindex('.')])

        recomendations_to_user=[]

        for recommendation in lstRecommendations:
            # print(recommendation.name)
            recommendObj = {}
            recommendObj["name"] = recommendation.name[:recommendation.name.rindex('.')].rsplit("-",1)[0]
            recommendObj["description"] = ""
            recommendObj["link"] =  recommendation.name[:recommendation.name.rindex('.')] + '.pdf'
            recommendObj["Year"] = recommendation.year
            recommendObj["Size"] = round((os.path.getsize("incoming_data/" + recommendObj["link"])/1000),1)
            recomendations_to_user.append(recommendObj)

        # print('Sending recommendation to front end')
        # print(lstRecommendations)
        # print("min")
        # print(user_data.user_min_value)
        # print("max")
        # print(user_data.user_max_value)
        return {"suggestions": recomendations_to_user}

@app.get("/pdf/{fileName}")
def view_pdf(request: Request, fileName: str):
    print(fileName)
    return templates.TemplateResponse("./public/pdf.html", {"request": request, "pdf_file": fileName, "pdf": fileName.rsplit("-",1)[0], "doc_history_count": doc_history_count})

@app.get("/viewhistory", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("./public/viewHistory.html", {"request": request})

@app.post("/pdfdata")
def recomended_things(request: Response, user_data: delete_user_history):
    print("pdfpdfpdfpdfpdfpdfpdfpdfpdfpdfpdf")
    clickedDocs = user_data.user_click_history.split(',')
    data_to_check_history = []
    for doc in clickedDocs:
        history_to_user = {}
        docPath = str(os.path.join("ScrapedPDFs",(doc.replace(".pdf",".txt"))))
        history_to_user["name"] = str(doc.rsplit("-",1)[0])
        history_to_user["link"] = str("/pdf/" + doc)
        history_to_user["year"] = doclistData[docPath]["Year"]
        history_to_user["size"] = doclistData[docPath]["Size"]
        data_to_check_history.append(history_to_user)
    # close file
    return {"history": data_to_check_history}