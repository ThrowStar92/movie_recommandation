from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import pandas as pd
import numpy as np

# Create your views here.

def sums(num):
    new_num = num*2
    return new_num

genres = ["액션","코미디","공포"]

class model1(APIView):
    
    def get(self, request):

        return Response({"data":"data"})

    def post(self, request):
        
        input_data = request.data

        numberA = input_data["numA"]
        numberB = input_data["numB"]

        resultA = sums(numberA)
        resultB = sums(numberB)
        returnD = resultA + resultB

        # print(input_data["data"])

        return Response(returnD)
    
class model_filtering(APIView):

    def get(self, request):
        # response = self.filtering(self.genres, self.movie_list)
        return Response({"genres": "genres"})

    def post(self, request):
        input_data = request.data
        genres = input_data.get("genres", [])
        filtered_movies = self.filtering(genres)
        return Response(filtered_movies)

    
    def filtering(self, genres) : 
        movie_list = pd.read_excel('./movie_1822_1.xlsx')
        movie_list['genre'] = movie_list['genre'].replace(np.nan, " ")
        fmovie = pd.DataFrame()
        for g in genres : 

            fmovie = fmovie.append(movie_list[movie_list["genre"].str.contains(g)])

        fmovie = fmovie.drop_duplicates("title")
        
        fmovie_sort = fmovie.sort_values(by=fmovie.columns[8],ascending = False)
        fmovie_sort_four = fmovie_sort.head(3)
        fmovie_sort_four_code = fmovie_sort_four['code']
        
        return fmovie_sort_four_code.to_dict()

class model_similarity(APIView):    

    def get(self, request):
        # response = self.filtering(self.genres, self.movie_list)
        return Response({"code_num": "code"})

    
    def post(self, request):
        
        # print("post", request)
        input_data = request.data
        code_num = input_data.get("code_num")
        # try:
        #     similar_movies = self.similarity(code_num)
        #     return Response(similar_movies)
        # except ValueError as e:
        #     return Response({"error": str(e)})

        similiarity_movies = self.similarity(code_num)
        return Response(similiarity_movies)

    def similarity(self,code_num):
        
        movie_list = pd.read_excel('./movie_1822_1.xlsx')
        movie_10 = pd.read_excel('./movie_2023_box.xlsx')   

        movie_one = movie_list.loc[movie_list["code"] == int(code_num)]
        # print(movie_one)
        movie_one_gen = movie_one["genre"]
        # return Response("{}")
        # print(type(movie_one_gen))
        movie_sim = pd.concat([movie_one,movie_10], axis = 0,ignore_index = True)
        # print(movie_sim)
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

        return similar_movies['code']

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
        
        
    # count_similar_movies_gen = find_sim_movie(movie_sim,count_sim_sorted_ind_gen,code_num,top_n=20)
    # print(count_similar_movies_gen)


    # def similarity(self,code_num):
        movie_list = pd.read_excel(r'C:\movie_list\movies_list\movies\movie_1822_1.xlsx')
        movie_10 = pd.read_excel(r'C:\movie_list\movies_list\movies\movie_2023_box.xlsx')   

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
        
        count_similar_movies = find_sim_movie(movie_sim,count_sim_sorted_ind,code_num,top_n=20)
        TF_similar_movies = find_sim_movie(movie_sim,TF_sim_sorted_ind,code_num,top_n=20)
        conbined_similar_movies = find_sim_movie(movie_sim,conbined_sim_sorted_ind,code_num,top_n=20)
        count_similar_movies_gen = find_sim_movie(movie_sim,count_sim_sorted_ind_gen,code_num,top_n=20)
        TF_similar_movies_gen = find_sim_movie(movie_sim,TF_sim_sorted_ind_gen,code_num,top_n=20)
        all_conbined_similar_movies = find_sim_movie(movie_sim,all_combined_sim_sorted_ind,code_num,top_n=20)
        # 일단 하나의 종류만 return한다 생각을 해야한다.
        return all_conbined_similar_movies[['title','code']][1:]



# class model2(APIView):
#     def get(self, request,name):

#         your_name = name

#         data = "안녕하세요" + your_name  + "입니다"
#         return Response(data)
    




     