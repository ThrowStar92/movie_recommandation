from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import pandas as pd
import numpy as np
import os
import json
from pathlib import Path
from django.conf import settings
import random
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
        print("장르", genres)
        filtered_movies = self.filtering(genres.split(','))
        return Response(filtered_movies)

    # def post(self, request):
    #     input_data = request.data
    #     genres = input_data.get("genres", [])
    #     filtered_movies = self.filtering(genres)
    #     return Response(filtered_movies)

    
    def filtering(self, genres) : 
        movie_list = pd.read_excel(r'./movies/movie_0222.xlsx')
        # movie_list['genre'] = movie_list['genre'].replace(np.nan, " ")
        fmovie = pd.DataFrame()
        for g in genres : 

            fmovie = fmovie.append(movie_list[movie_list["genre"].str.contains(g)])

        fmovie = fmovie.drop_duplicates("title")
        fmovie_sort = fmovie.sort_values(['rate'],ascending = False).head(9)

        fmovie_sort_random = fmovie_sort.sample(n=9 , random_state=random.seed())
        fmovie_sort_four_code = fmovie_sort_random['code']
        result_code = fmovie_sort_four_code.tolist()
        fmovie_sort_four_title = fmovie_sort_random['title']
        result_title = fmovie_sort_four_title.tolist()

        res_data = []
        for title, code in zip(result_title, result_code):
            res_data.append({"code": code, "title": title})
        dict_data = {"data": res_data}
        json_obj = json.dumps(dict_data, ensure_ascii=False)
        return json_obj
    # print(type(json_obj))
        # print(res_data)
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
        movie_list = pd.read_excel(r'./movies/movie_0222.xlsx')
        movie_10 = pd.read_excel(r'./movies/movie_box_test.xlsx')

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

        return similar_movies

    def find_sim_movie(self,df, sorted_ind, code_num, top_n=20):
    
        # 인자로 입력된 movies_df DataFrame에서 'title' 컬럼이 입력된 title_name 값인 DataFrame추출
        title_movie = df[df['code'] == code_num]

        # title_named을 가진 DataFrame의 index 객체를 ndarray로 반환하고 
        # sorted_ind 인자로 입력된 genre_sim_sorted_ind 객체에서 유사도 순으로 top_n 개의 index 추출
        title_index = title_movie.index.values
        similar_indexes = sorted_ind[title_index, :(top_n)]
        similar_indexes = similar_indexes.reshape(-1)
        
        result_data = []
        for idx in similar_indexes:
            # result_data.append({"code": str(df.iloc[idx]["code"]), "title": df.iloc[idx]["title"]})
            # result_data.append(str(df.iloc[idx]))
            result_data.append(str(idx))
        print(result_data[1:4])
        dict_data = {"data": {1:result_data[1],2:result_data[2],3:result_data[3]}}

        json_obj = json.dumps(dict_data, ensure_ascii=False)
        return json_obj 
        




     