import os
import re

from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.layout import LAParams
from pdfminer.converter import PDFPageAggregator
# from pdfminer.pdfinterp import PDFTextExtractionNotAllowed
from tinyDB import tiny_db_add_data

# from fastapi import APIRouter

# Add document categories
doc_cat_file = 'documentcategory.txt'

# router = APIRouter()

# convert one PDF file to TXT file
# @router.get("/Pdf2Txt/onePdfToTxt")
def onePdfToTxt(filepath, outpath):   
    try:        
        fp = open(filepath, 'rb')
        outfp = open(outpath, 'w', encoding='utf-8')
        parser = PDFParser(fp)
        doc= PDFDocument(parser)
        # parser.set_document(doc)
        # doc.set_parser(parser)
        
        # doc.initialize("")
        
        if not doc.is_extractable:
            #raise PDFTextExtractionNotAllowed
            pass

        else:
            resource = PDFResourceManager()
            
            laparams = LAParams()
            
            device = PDFPageAggregator(resource,laparams=laparams)
            
            interpreter = PDFPageInterpreter(resource,device)
            
            for page in enumerate(PDFPage.create_pages(doc)):
                
                interpreter.process_page(page[1])
                
                layout = device.get_result()
                
                for out in layout:
                    
                    if hasattr(out,"get_text"):
                        text=out.get_text()
                        outfp.write(text+'\n')
            fp.close()
            outfp.close()
    except Exception as e:
         print (e)


# convert all PDF files in a folder to TXT files
# @router.get("/Pdf2Txt/manyPdfToTxt")
def manyPdfToTxt (fileDir):
    files = os.listdir(fileDir)
    tarDir = 'ExtractedText'
    if not os.path.exists(tarDir):
        os.mkdir(tarDir)
    replace = re.compile(r'\.pdf',re.I)
    for file in files:
        filePath = fileDir+'\\'+file
        outPath = tarDir+'\\'+re.sub(replace, '', file)+'.txt'
        onePdfToTxt(filePath, outPath)
        print("saved in "+outPath)

# PDF with categories upload
def onePdfToTxtWithCategories(filepath, outpath, fileCategories):
    try:
        fp = open(filepath, 'rb')
        outfp = open(outpath, 'w', encoding='utf-8')
        parser = PDFParser(fp)
        doc= PDFDocument(parser)
        
        if not doc.is_extractable:
            #raise PDFTextExtractionNotAllowed
            pass

        else:
            resource = PDFResourceManager()
            laparams = LAParams()
            device = PDFPageAggregator(resource,laparams=laparams)
            interpreter = PDFPageInterpreter(resource,device)
            
            for page in enumerate(PDFPage.create_pages(doc)):
                interpreter.process_page(page[1])
                layout = device.get_result()
                for out in layout:
                    if hasattr(out,"get_text"):
                        text=out.get_text()
                        outfp.write(text+'\n')
            fp.close()
            outfp.close()

            # Add to document categories
            openFile = open(doc_cat_file,"a", encoding='utf-8')
            sizeoffile = round((os.path.getsize(filepath)/1000),1)
            openFile.write(os.path.splitext(os.path.basename(outpath))[0] + '.txt' + "\t" + '"' + str(fileCategories) + '"' + "\t" + str(sizeoffile) + "\n")
            openFile.close()

            tiny_db_add_data(fileCategories)
    except Exception as e:
         print (e)