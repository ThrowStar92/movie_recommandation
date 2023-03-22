from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import pandas as pd
import numpy as np
import os
from pathlib import Path
from django.conf import settings

# Create your views here.

class home(APIView) :
    def get(self, request) :
        filter = "요청 주소는  <filter>: filter/장르이고, 여러개 보낼시 장르1, 장르2, 장르3 등..  /   <similar>: similar/영화코드입니다."
        
        return Response(filter)


class filter(APIView) :
    def get(self, request) :
        filter = "요청 주소는  <filter>: filter/장르이고, 여러개 보낼시 장르1, 장르2, 장르3 등.. //"
        return Response(filter + "형식에 맞춰서 보내주세요")

class similar(APIView) :
    def get(self, request) :
        filter = "요청 주소는 <similar>: similar/영화코드입니다. //"

        return Response(filter + "형식에 맞춰서 보내주세요")


class model_filtering(APIView):

    def get(self, request, genres):
        print(genres)
        filtered_movies = self.filtering(genres)
        return Response(filtered_movies)

    # def post(self, request):
    #     input_data = request.data
    #     genres = input_data.get("genres", [])
    #     filtered_movies = self.filtering(genres)
    #     return Response(filtered_movies)

    
    def filtering(self, genres) : 
        movie_list = pd.read_excel(r'./movies/movie_1822_1.xlsx')
        movie_list['genre'] = movie_list['genre'].replace(np.nan, " ")
        fmovie = pd.DataFrame()
        for g in genres : 

            fmovie = fmovie.append(movie_list[movie_list["genre"].str.contains(g)])

        fmovie = fmovie.drop_duplicates("title")
        
        fmovie_sort = fmovie.sort_values(by=fmovie.columns[8],ascending = False)
        fmovie_sort_four = fmovie_sort.head(9)
        fmovie_sort_four_code = fmovie_sort_four['code']
        
        return fmovie_sort_four_code.to_dict()

class model_similarity(APIView):    

    def get(self, request, movieCode):
        movieCode
        print(movieCode)
        
        similiarity_movies = self.similarity(movieCode)
        return Response(similiarity_movies)
    
    
    # def post(self, request):
        
    #     input_data = request.data
    #     code_num = input_data.get("code_num")

    #     similiarity_movies = self.similarity(code_num)
    #     return Response(similiarity_movies)

    def similarity(self,code_num):
        movie_list = pd.read_excel(r'./movies/movie_1822_1.xlsx')
        movie_10 = pd.read_excel(r'./movies/movie_2023_box.xlsx')

        movie_one = movie_list.loc[movie_list["code"] == int(code_num)]
        movie_one_gen = movie_one["genre"]
        movie_sim = pd.concat([movie_one,movie_10], axis = 0,ignore_index = True)
        token_pattern = r"(?u)\b\w+\b"

        # CV-genre
        count_vect_gen = CountVectorizer(min_df=0,ngram_range= (1,2),token_pattern=token_pattern)
        count_mat_gen = count_vect_gen.fit_transform(movie_sim['genre'])
        count_cos_sim_gen = cosine_similarity(count_mat_gen,count_mat_gen)
        count_sim_sorted_ind_gen = count_cos_sim_gen.argsort()[:, ::-1]
                
        # CV
        count_vect = CountVectorizer(min_df=0,ngram_range= (1,2),token_pattern=token_pattern)
        count_mat = count_vect.fit_transform(movie_sim['story'])
        count_cos_sim = cosine_similarity(count_mat,count_mat)
        count_sim_sorted_ind = count_cos_sim.argsort()[:, ::-1]
        
        # TF-IDF-genre
        TF_IDF_gen = TfidfVectorizer(min_df=0,ngram_range= (1,2),token_pattern=token_pattern)
        TF_mat_gen = TF_IDF_gen.fit_transform(movie_sim['genre'])
        TF_cos_sim_gen = cosine_similarity(TF_mat_gen,TF_mat_gen)
        TF_sim_sorted_ind_gen = TF_cos_sim_gen.argsort()[:, ::-1]
        
        # TF-IDF
        TF_IDF = TfidfVectorizer(min_df=0,ngram_range= (1,2),token_pattern=token_pattern)
        TF_mat = TF_IDF.fit_transform(movie_sim['story'])
        TF_cos_sim = cosine_similarity(TF_mat,TF_mat)
        TF_sim_sorted_ind = TF_cos_sim.argsort()[:, ::-1]

        # 가중치
        weight_count = 0.5
        weight_tfidf = 0.5
        weight_count_gen = 0.5
        weight_tfidf_gen = 0.5
        
        # 혼합
        combined_cos_sim = (weight_count * count_cos_sim) + (weight_tfidf * TF_cos_sim)
        conbined_sim_sorted_ind = combined_cos_sim.argsort()[:, ::-1]
        
        all_combined_cos_sim = (weight_count * count_cos_sim) + (weight_tfidf * TF_cos_sim) + (weight_count_gen * count_cos_sim_gen) + (weight_tfidf_gen * TF_cos_sim_gen)
        all_combined_sim_sorted_ind = all_combined_cos_sim.argsort()[:, ::-1]
                
        similar_movies = self.find_sim_movie(movie_sim, all_combined_sim_sorted_ind, int(code_num), top_n=20)

        return similar_movies['code'][1:4]

    def find_sim_movie(self,df, sorted_ind, code_num, top_n=20):
    
        # 인자로 입력된 movies_df DataFrame에서 'title' 컬럼이 입력된 title_name 값인 DataFrame추출
        title_movie = df[df['code'] == code_num]

        # title_named을 가진 DataFrame의 index 객체를 ndarray로 반환하고 
        # sorted_ind 인자로 입력된 genre_sim_sorted_ind 객체에서 유사도 순으로 top_n 개의 index 추출
        title_index = title_movie.index.values
        similar_indexes = sorted_ind[title_index, :(top_n)]

        # 추출된 top_n index들 출력. top_n index는 2차원 데이터 임. 
        #dataframe에서 index로 사용하기 위해서 1차원 array로 변경
        print(similar_indexes)
        similar_indexes = similar_indexes.reshape(-1)

        return df.iloc[similar_indexes]    
        




     