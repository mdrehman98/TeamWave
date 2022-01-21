from django.shortcuts import render
from django.http import HttpResponse
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests
import datetime

from uuid import uuid4
import os
from django.forms import model_to_dict
from pathlib import Path
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.core.paginator import Paginator
from django.db.models import Count
from .models import *
#import firebase_admin
#from firebase_admin import credentials
#from firebase_admin import messaging
#from .serializers import *
from stackapi import StackAPI
from ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
# Create your views here.
def home(request):
	return render(request,'index.html')

def get_title_from_index(index):
	df = pd.read_csv("movie_dataset1.csv",encoding='latin-1')
	df['title']=df['title'].str.upper()
	return df[df.index == index]["title"].values[0]

def get_index_from_title(title):
	df = pd.read_csv("movie_dataset1.csv",encoding='latin-1')
	df['title']=df['title'].str.upper()
	try:
		return df[df.title == title]["index"].values[0]
	except:
		print("Movie not found")
		
def search(request):
	df = pd.read_csv("movie_dataset1.csv",encoding='latin-1')
	df['title']=df['title'].str.upper()
	list1=list(df['title'])
	features = ['keywords','cast','genres','director']
	for feature in features:
		df[feature] = df[feature].fillna('')

	def combine_features(row):
		try:
			return row['keywords'] +" "+row['cast']+" "+row["genres"]+" "+row["director"]
		except:
			print("Error:", row)

	df["combined_features"] = df.apply(combine_features,axis=1)

	cv = CountVectorizer()

	count_matrix = cv.fit_transform(df["combined_features"])
	
	cosine_sim = cosine_similarity(count_matrix)
	num1=request.GET['message']
	movie_caps=num1.upper()
	for lists in list1:
		if movie_caps in lists:
			movie_user_likes=lists
			break
		
	try:	
		movie_index= get_index_from_title(movie_user_likes)
	except:
		return HttpResponse("<h1>Movie not found</h1><br> Please look at the 'Movies' Section for a sample movie")
	similar_movies =  list(enumerate(cosine_sim[movie_index]))
	sorted_similar_movies = sorted(similar_movies,key=lambda x:x[1],reverse=True)

	i=0
	title1=[]
	for element in sorted_similar_movies:
			title1+=[get_title_from_index(element[0])]
			i=i+1
			if i>10:
				break
	print(title1)

	

	return render(request,'result.html',{'title':title1,'movie_user_likes':movie_user_likes})


class getQuestions(APIView):
	permission_classes = [AllowAny, ]
	@method_decorator(ratelimit(key='ip', rate='5/m', method='GET',block=True))
	@method_decorator(ratelimit(key='ip', rate='100/d', method='GET',block=True))
	@method_decorator(cache_page(60))
	def get(self,request):
		SITE = StackAPI('stackoverflow')
		minimum=request.GET.get('min')
		fromdate=request.GET.get('fromdate')
		todate=request.GET.get('todate')
		page=int(request.GET.get('page'))
		maximum=request.GET.get('max')
		sort=request.GET.get('sort')
		order=request.GET.get('order')
		answers=int(request.GET.get('answers'))
		accepted=request.GET.get('accepted')
		closed=request.GET.get('closed')
		migrated=request.GET.get('migrated')
		notice=request.GET.get('notice')
		wiki=request.GET.get('wiki')
		nottagged=request.GET.get('nottagged')
		tagged=request.GET.get('tagged')
		title=request.GET.get('title')
		user=request.GET.get('user_ids')

		if 'page_size' in request.GET:
			page_size=request.GET['page_size']
			SITE.page_size=int(page_size)
		if 'max_pages' in request.GET:
			max_pages=request.GET['max_pages']
			SITE.max_pages=int(max_pages)
		question=SITE.fetch('questions',min=minimum,max=maximum,todate=todate,fromdate=fromdate,page=page,order=order,sort=sort,answers=answers,closed=closed,notice=notice,wiki=wiki,title=title)
		#print(question)
		#return CustomResponse().successResponse(description="Number of Departments counted", data=question)
		return render(request,'result.html',{'details':question['items']})
	





	