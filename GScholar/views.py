'''             Graphical representation of paper publications               '''

#Import statements
from django.shortcuts import render
from django.shortcuts import redirect
from django.db import connections
from django.db.models import Count
from django.http import JsonResponse
from django.http import HttpResponse
from bs4 import BeautifulSoup,SoupStrainer
from urllib2 import urlopen
import time
import subprocess
import urllib2
import timeit
import itertools
import operator
import os
import math
import re
import unicodedata
import string
import json
import codecs
from django.core.files.storage import *
import csv
from copy import *
from django.conf import settings

def process(request):
	#List declaration
	NAME=request.POST['firstname']
	title=[] #name of paper publications
	citlinks=[] #Web links to the papers that have cited corresponding papers in title[]
	co_authors=[] #All the coauthors put together in correspondance with the paper title
	no_of_citations=[] #Number of citations for the corresponding paper
	distinct_co_authors=[] #Distinct coauthors generated in a different order
	no_of_shared_papers=[] #Total number of shared papers of an author in the current order of distinct coauthors
	no_of_shared_citations=[] #Total number of shared citations
	years=[] #Year in which corresponding paper of title list was published
	author_year=[] #Year corresponding to the author of every paper
	title_author=[] #To hold the paper title of each author
	listOfFiles=[] #To hold the list of json files
	flag=1 #Flag variable
	x=0

	#Dictionary declaration containing key-value pairs
	dist={}#To hold the coauthor-shared citation pairs
	dic={}#To hold the coauthor-shared paper pairs
	year_dict={}#To hold the coauthor-year pairs
	title_dict={}#To display all the common papers

	#Function that removes all the non-ASCII characters of a string and returns this string
	def strip_non_ascii(string):
		stripped = (c for c in string if 0 < ord(c) < 127)
		return ''.join(stripped)

	#User input fot main author name and changing them to lower letters
	#MUST BE TAKEN FROM HTML USING DJANGO
	global name, listOfFiles,filename
	listOfFiles=[]
	name=NAME
	person = name
	person = person.lower().strip()
	global filename1, filename
	filename1=person.replace(" ","_")+'_min_max.json'
	filename=person+'1.json'
	if (os.path.isfile(os.path.join(settings.MEDIA_ROOT, filename1))):
		fileValues=open(os.path.join(settings.MEDIA_ROOT, filename1), 'r')
		jsonFileContent=json.load(fileValues)
		fileCount=int(jsonFileContent["fileCount"])
		for i in range(1,fileCount+1):
			tempFile=person+str(i)+".json"
			if (os.path.isfile(os.path.join(settings.MEDIA_ROOT, tempFile))):
				isFile=True
				listOfFiles.append(tempFile)
			else:
				isFile=False
				listOfFiles=[]
				break
		if isFile:
			person=person.capitalize()
			return render(request,'GScholar/dummy.html',globals())
	person2 = person.replace(" ","+") # Replacing the white spaces with +

	#Tokenizing the person variable, so that if the person name or if the first and last names of the person are reversed, the name denotes the same person
	if " " in person:
		t=person.split(" ")
		if len(t)==2:
				personrev=str(t[1]+" "+t[0])
		else:
				personrev=person
		person_init=""
		for i in xrange(len(t)-1):
				k=t[i]
				person_init+=k[0]
		person_init+=" "+t[len(t)-1]
	else:
		personrev=person
		person_init=person

	#URL of the initial Google Scholar page on entering the author
	person2=person2.replace(" ","+")
	begin_url = "https://scholar.google.co.in/scholar?hl=en&q="+person2

	#To have a continous connection with the server by sending a request to it
	hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
		   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		   'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
			'Accept-Encoding': 'none',
		   'Accept-Language': 'en-US,en;q=0.8',
		   'Connection': 'keep-alive'}
	req = urllib2.Request(begin_url,headers=hdr)

	#The html content of the initial page of Google Scholar
	page = urllib2.urlopen(req)
	# begin_url="https://www.google.com"
	# phpfile=os.path.join(settings.MEDIA_ROOT, "scrape.php")
	# proc = subprocess.Popen("php scrape.php https://scholar.google.co.in/scholar?hl=en q=" + person2, shell=True, stdout=subprocess.PIPE)
	# proc = subprocess.Popen("php scrape.php page1.txt", shell=True, stdout=subprocess.PIPE)
	# page = proc.stdout.read()
	
	# time.sleep(5)
	# abc=open("data.txt","r")
	# page=abc.read()
	#To scrape the required html tag contents, which are img and h4
	links = SoupStrainer(['img','h4'])

	#Parsing the html content
	soup1 = BeautifulSoup(page, parse_only=links)
	
	
	#An author with a profile would contain a feather image (/intl/en/scholar/feather-72.png)
	#Scraping the required contents is based on the condition if the parsed html page consists of an image, which is the only image in the page

	if (soup1.find("img")):
		#""AUTHORS WITH A PROFILE""
		#Hyperlink text of the author to move to the next page, ie author profile
		BASE_URL = soup1.find("h4", attrs={"class": "gs_rt2"}).a.get('href')

		#The url of the author's profile
		BASE_URL = "https://scholar.google.com"+BASE_URL

		#print "PROFILE\n"
		prof=1
		#x variable keeping the starting paper number of that page which is incremented by 100 in every loop
		while flag:
			#Author's profile page url along with the starting paper and total no of papers in a page(maximum of 100)
			BSE_URL = BASE_URL+"&cstart="+str(x)+"&pagesize=100"

			#To have a continous connection with the server by sending a request to it
			hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
							'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
							'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
							'Accept-Encoding': 'none',
							'Accept-Language': 'en-US,en;q=0.8',
							'Connection': 'keep-alive'}
			req = urllib2.Request(BSE_URL,headers=hdr)
			#The html content of the profile page of the author
			html = urllib2.urlopen(req)
			# divByAnd=BSE_URL.split('&')
			# urlSendPhp=' '.join(divByAnd)
			# proc = subprocess.Popen("php scrape.php "+urlSendPhp, shell=True, stdout=subprocess.PIPE)
			# proc = subprocess.Popen("php scrape.php prpage1.txt", shell=True, stdout=subprocess.PIPE)

			# html=proc.stdout.read()
			# html=abc.read()
			#Scraping only the button tags of the html content
			links = SoupStrainer("button")
			soup = BeautifulSoup(html, parse_only=links)

			#flag is set 0 if the page denotes the end of all papers indicated by a dimnished right arrow at the end of the page
			for end in soup.find_all("button", attrs={"class": "gs_btnPR gs_in_ib gs_btn_half gs_btn_srt gs_dis"}):
				flag=0

			#The html content of the profile page of the author
			html = urllib2.urlopen(req)
			# proc = subprocess.Popen("php scrape.php "+urlSendPhp, shell=True, stdout=subprocess.PIPE)
			# proc = subprocess.Popen("php scrape.php prpage1.txt", shell=True, stdout=subprocess.PIPE)
			# html = proc.stdout.read()
			#Scraping a, division and span tags of the html content
			links = SoupStrainer(['a','div','span','td'])
			soup = BeautifulSoup(html, parse_only=links)

			#Scraping the total no of citations and h-index from profile page
			citation_indices=soup.find_all('td', attrs={"class": "gsc_rsb_std"})
			total_no_of_citations=int(citation_indices[0].get_text())
			h_index=citation_indices[2].get_text()
							
			#Class gsc_a_at represents the paper title
			for link in soup.find_all('a', attrs={"class": "gsc_a_at"}):
				#Appending the utf-8 encoded paper title to title list 
				title.append(strip_non_ascii(str(link.get_text().encode("utf-8",'ignore'))).replace("\"",""))

				#Searching for the immediate list of coauthors for that paper
				co=link.findNext('div',attrs={"class" : "gs_gray"})
				#Appending the utf-8 encoded coauthors list to the python list
				co_authors.append(strip_non_ascii(str(co.text.encode("utf-8",'ignore'))))

				#Searching for the total number of citations for that paper
				no_of_cites=link.findNext("a",attrs={"class": "gsc_a_ac"})
				#Appending the link to all the papers that have cited this particular paper into the list citlinks
				citlinks.append(str(no_of_cites.get('href').encode("utf-8",'ignore')))

				#Appending the total number of citations of that paper to the list no_of_citations only if there is no unicode error in the text
				s=""
				try:
					s=s+str(no_of_cites.get_text())
				except UnicodeEncodeError:
					no_of_citations.append(0)
				else:
					no_of_citations.append(int((no_of_cites.get_text().encode("utf-8",'ignore'))))

				#Searching for the published year of that paper
				ye=link.findNext("span",attrs={"class": "gsc_a_h"})
				#Appending the text content of the year to the list year
				if(ye.get_text()!=""):
					years.append(str(ye.get_text().encode("utf-8",'ignore')))
				else:
					years.append(str(''))
			x+=100

		#Now the length of the lists title,co_authors,years,no_of_citations,citlinks are same
		#For every index of the title list, ie from 0 to length of title
		for i in xrange(len(title)):
		 #Splitting the coauthors from its normal list on a ',' 
		 for s in co_authors[i].split(','):
			 #Removing all those coauthors that are the main author itself or contain ellipses in them
			 if s.lower!=person_init and person_init not in s.lower() and s.lower()!=person and person not in s.lower() and s.lower()!=personrev and personrev not in s.lower() and ' ...' not in s and '...'!=s and "\\" not in s and s!=" ":
				#Removing initial white spaces and converting author to lower case.Appending the coauthor to the list
				distinct_co_authors.append(s.lower().strip())
				#For every coauthor, the corresponding no of ciations are appended to the list
				no_of_shared_citations.append(no_of_citations[i])
				#For every coauthor, the corresponding year of publication is appended to the list
				author_year.append(years[i])
				#For every author, the corresponding paper title is appended
				title_author.append(title[i])

			

	else:
		'''   N-O-N P-R-O-F-I-L-E A-U-T-H-O-R-S  '''
		#print "NON - PROFILE\n"
		prof=0
		#To keep the count of pages
		x=0

		#Looping first 3 Google scholar pages
		while(x<30):
				#URL for the Google Scholar pages without citation paper links where start indiactes the paper count
				b_url = "https://scholar.google.co.in/scholar?start="+str(x)+"&q="+person2+"&hl=en&as_sdt=0,5&as_vis=1"
				#To have a continous connection with the server by sending a request to it
				hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
					'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
					'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
					#'Accept-Encoding': 'none',
					'Accept-Language': 'en-US,en;q=0.8',
					'Connection': 'keep-alive'}
				req = urllib2.Request(b_url,headers=hdr)
				#Opening the url page
				page = urllib2.urlopen(req)
				# divByAnd=b_url.split('&')
				# urlSendPhp=' '.join(divByAnd)
				# proc = subprocess.Popen("php scrape.php " + urlSendPhp, shell=True, stdout=subprocess.PIPE)
				# page = proc.stdout.read()
				# phpfile=os.path.join(settings.MEDIA_ROOT, "scrape.php")
				# proc = subprocess.Popen("php "+phpfile+" " + b_url, shell=True, stdout=subprocess.PIPE)
				# page = proc.stdout.read()
				#Scraping only h3,div and a tags of the html content
				links = SoupStrainer(['h3','div','a'])
				#Parsing the html content
				soup1 = BeautifulSoup(page, parse_only=links)

				#Finding all the required attributes
				for link in soup1.find_all("h3", attrs={"class": "gs_rt"}):
					#Checking if the title has an a tag
					if link.a:
							#Extracting only text of the hyperlink of title to the list
							title.append(strip_non_ascii(str(link.a.get_text().encode("utf-8",'ignore'))).replace("\"",""))
					else:
							#Extracting the text of the title and appending to the list
							title.append(strip_non_ascii(str(link.get_text().encode("utf-8",'ignore'))).replace("\"",""))

					#Finding the complete list of all coauthors
					co=link.findNext('div',attrs={"class" : "gs_a"})
					#Appending the string to the list
					co_authors.append(strip_non_ascii(str(co.text.encode("utf-8",'ignore'))))

					

					#Finding the link for the papers that have cited this paper
					no_of_cites=link.findNext("div",attrs={"class": "gs_fl"})

					#Tokenizing this text content to obtain the no of citations for this paper
					spl=no_of_cites.a.get_text().encode("utf-8",'ignore')
					
					#Appending both citation links and no of citations based on the occurrence of the word "Cited"
					if spl[0:5]=="Cited":
							citlinks.append("https://scholar.google.co.in"+str(no_of_cites.a.get('href').encode("utf-8",'ignore')))
							if(spl[9:]==""):
									no_of_citations.append(0)
							else:
									no_of_citations.append(int(spl[9:]))
									
					else:
							citlinks.append("")
							no_of_citations.append(0)
				#Incrementing x for next page    
				x+=10
		#Calculating total no of cit
		total_no_of_citations=sum(no_of_citations)
		temp_noc=list(no_of_citations)
		temp_noc=sorted(temp_noc,reverse=True)
		
		#Calculating h-index
		h_index=0
		for i,j in enumerate(temp_noc):
			if j>=i+1:
				h_index=i+1

			else:
				break
		
		
		#Extracting the year of publication from the list of coauthors
		for i in xrange(len(title)):
			for s in co_authors[i].split(','):
				  
				if "-" in s:
						q=s.split('-')
						q[0]=q[0].strip()
						if q[0].isdigit():
							years.append(str(q[0]))
						
			if len(years)!=i+1:
				years.append('')



		#Appending the attributes to their corresponding lists
		for i in xrange(len(title)):
		 for s in co_authors[i].split(','):
			#Removing the non-ASCII characters in the author name and changing to lower case
			s=s.lower()
			#Checking if the main author and other characters are not present in the distinct co authors list
			if s!=person and s!="" and s!=personrev and personrev not in s and s!=person_init and person_init not in s and "..."!=s:
					
						
					#Appending all the attributes
					if "-" in s:
							q=s.split('-')
							q[0]=q[0].strip()
							if "..." in q[0]:
								q[0]=q[0][:-3]
							if not q[0].isdigit():
									distinct_co_authors.append(q[0])
									no_of_shared_citations.append(no_of_citations[i])
									author_year.append(years[i])
									title_author.append(title[i])
					else:
							s=s.strip()
							if not s.isdigit():
									distinct_co_authors.append(s)
									no_of_shared_citations.append(no_of_citations[i])
									author_year.append(years[i])
									title_author.append(title[i])
		
	#Appending all the papers of an author in a dictionary
	for i in xrange(len(distinct_co_authors)):
		if distinct_co_authors[i] in title_dict.keys():
			title_dict[distinct_co_authors[i]].append(title_author[i])
		else:
			title_dict[distinct_co_authors[i]]=[]
			title_dict[distinct_co_authors[i]].append(title_author[i])
				
	#Finidng out the total number of shared citations for every author using the dictionary
	for i in xrange(len(distinct_co_authors)):
		if distinct_co_authors[i] in dist.keys():
			dist[distinct_co_authors[i]]+=no_of_shared_citations[i]
		else:
			dist[distinct_co_authors[i]] =no_of_shared_citations[i]

		
	#Finidng out the most recent year the main author has worked with the coauthor 
	for i in xrange(len(distinct_co_authors)):
		if distinct_co_authors[i] in year_dict.keys():
			if author_year[i]>year_dict[distinct_co_authors[i]]:
				year_dict[distinct_co_authors[i]]=author_year[i]
		else:
			year_dict[distinct_co_authors[i]] =author_year[i]

	#Removing all the duplicates in the list    
	distinct_co_authors=list(set(distinct_co_authors))

	#Removing those coauthors whose shared citations is zero
	for i in distinct_co_authors:
		if dist[i] == 0:
			#print i+"has to be removed"
			distinct_co_authors.remove(i)
			del dist[i]
			del year_dict[i]
			del title_dict[i]
		
	#To find the total number of shared papers of every author
	for a in distinct_co_authors:
		index=0
		for i in xrange(len(title)):
			if a in co_authors[i].lower():
				index+=1
		no_of_shared_papers.append(index)
		
	#Sorting out the coauthors list in the descending order of no of shared papers
	for f,b in itertools.izip(distinct_co_authors,no_of_shared_papers):
		dic.update({f:b})
	#Sorted key value pairs are stored in the variable req
	req = sorted(dic.items(), key=operator.itemgetter(1),reverse=True)

	#To find the maximum and minimum value of the shared citations
	max_nosc=max(dist.values())
	min_nosc=min(dist.values())
		
	#To find the maximum and minimum value of the shared papers
	max_nosp=max(dic.values())
	min_nosp=min(dic.values())
		
	#To find the maximum and minimum value of the year
	max_year=max(year_dict.values())
	year_without=[]
	year_without=(year_dict.values())
	while '' in year_without: year_without.remove('')   
	min_year=min(year_without)

	#Finding the g_index
	g_index=int(math.sqrt(total_no_of_citations))


	#JSON PART
	#Function that does the children nesting in the json file format
	#a & b are starting and ending indices
	global main_string,s,coauthors_string,pos
	def r(req,a,b):
		#The variables are declared global
		global main_string,s,coauthors_string,pos
		#Initial position is set to 0
		pos=0
		#i = author name and j=no of shared papers of author i
		for i,j in req[a:b]:
			#To represent the values in a proper range in d3
			#temp_nosp = j/max_nosp*20 if j/max_nosp*20>1 else 1
			#temp_nosc = dist[i]/max_nosc*20 if dist[i]/max_nosc*20>1 else 1
			#Replacing the special symbols with their corresponding values
			temp_title=str(";".join(title_dict[i]))
			s=coauthors_string.replace('$',i).replace('%',str(j)).replace('@',str(dist[i])).replace('*',str(year_dict[i])).replace('^',temp_title)
			s="["+s+"]"
			#To find the next position of string "[ ]" from the current position pos
			pos=main_string.find("[ ]",pos)
			#Modifying the main string
			main_string=(main_string[:pos]+ s +main_string[pos+3:])
			#Incrementing the position value 
			pos=pos+len(s)
		return
	global listOfFiles
	#Initial format of the main string
	temp_title=str(";".join(title))
	fileCount=1
	for author_count in range(0,len(req),90):
		main_string='{"papers":"'+temp_title+'","colour":"green","name":"'+person+'","edge_thickness":0,"node_diameter":20,"children":[#]}'
		#Initial format of the coauthors string
		coauthors_string='{"papers":"^","colour":"*","name":"$","edge_thickness":%,"node_diameter":@,"children":[ ]}'
		#Replacing the symbols with the corresponding values for the first coauthor
		#$=coauthor name; %=no of shared papers; @=no of shared citations; *=recent year; ^=common papers
		temp_title=str(";".join(title_dict[req[author_count][0]]))

		s=coauthors_string.replace('$',req[author_count][0]).replace('%',str(req[author_count][1])).replace('@',str(dist[req[author_count][0]])).replace('*',str(year_dict[req[author_count][0]])).replace('^',temp_title) + ","
		#Modifying the main string accordingly
		main_string=(main_string.replace("#",s)).encode("utf-8",'ignore')

		#Repeating the same procedure for next 29 authors
		for i,j in req[author_count+1:author_count+30]:
				#To represent the values in a proper range in d3
				temp_title=str(";".join(title_dict[i]))
				s=coauthors_string.replace('$',i).replace('%',str(j)).replace('@',str(dist[i])).replace('*',str(year_dict[i])).replace('^',temp_title)
				s=","+s+",]"
				main_string=(main_string.replace(',]',s))
		#Modifying main string in json format
		d=main_string.rfind(",")
		main_string= (main_string[:d]+main_string[d+1:])

		#Loop count variable
		k=author_count+30
		cnts=0
		while(k<len(req)):
				pos=0
				#Calling the function r
				r(req,k,k+30)  
				k+=30
				cnts+=1
				if cnts==2:
					break
		#Parsing the entire main string in json format
		parsed = json.loads(main_string)

		global filename, filename1
		#Appending the json format to the file, if the file already exists it is rewritten
		filename=person+str(fileCount)+".json"
		listOfFiles.append(filename)
		with open(os.path.join(settings.MEDIA_ROOT, filename), 'w') as outfile:
			json.dump(parsed, outfile, indent=3)
			fileCount+=1

		filename=person+"1.json"
	#Second json file for min and max
	string='{"max_nosp":'+str(max_nosp)+',"min_nosp":'+str(min_nosp)+',"max_nosc":'+str(max_nosc)+',"min_nosc":'+str(min_nosc)+',"max_year":'+str(max_year)+',"min_year":'+str(min_year)+',"total_cit":'+str(total_no_of_citations)+',"h_index":'+str(h_index)+',"g_index":'+str(g_index)+',"prof":'+str(prof)+',"fileCount":'+str(fileCount-1)+'}'
	csv_string='max_nosp,min_nosp,max_nosc,min_nosc,max_year,min_year,total_cit,h_index,g_index,prof\n'+str(max_nosp)+','+str(min_nosp)+','+str(max_nosc)+','+str(min_nosc)+','+str(max_year)+','+str(min_year)+','+str(total_no_of_citations)+','+str(h_index)+','+str(g_index)+','+str(prof)

	parsed1=json.loads(string)
		
	with open(os.path.join(settings.MEDIA_ROOT, filename1), 'w') as outfile:
		json.dump(parsed1, outfile,indent=3)
	global person
	person=person.capitalize()
	return render(request,'GScholar/dummy.html',globals())



	
def home(request):
	global name
	return render(request,'GScholar/main.html',globals())
	