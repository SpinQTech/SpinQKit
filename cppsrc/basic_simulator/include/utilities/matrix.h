/**
 * Copyright 2021 SpinQ Technology Co., Ltd.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef _MATRIX_H_
#define _MATRIX_H_

#include <iostream>
#include <complex>
#include <vector>

using namespace std;

template <typename T>
class matrix {
private:
    size_t             nrow;    // number of matrix rows
    size_t             ncol;    // number of matrix columns
    vector<vector<T>>  data;    // the data of matrix nrow x ncol

public:
    matrix();
    matrix(size_t nrow, size_t ncol);
    matrix(size_t nrow, size_t ncol, const T * data);
    matrix(const matrix<T> & M);
    ~matrix();

    void resize(size_t nrow, size_t ncol);
    size_t getRowNum() const;
    size_t getColNum() const;

    matrix<T> operator*(const matrix<T> & M) const;
    matrix<T> operator*(const T & x) const;
    matrix<T> operator+(const matrix<T> & M) const;
    matrix<T> operator-(const matrix<T> & M) const;
    matrix<T> operator=(const matrix<T> & M) const;
    vector<T> & operator[](size_t index);
    vector<T> operator[](size_t index) const;

    matrix<T> tensor(const matrix<T> & M) const;
    matrix<T> transform() const;
};

template <typename T>
inline bool operator==(const matrix<T> & m1, const matrix<T> & m2)
{
    size_t nrow = m1.getRowNum();
    size_t ncol = m1.getColNum();
    if (nrow != m2.getRowNum() || ncol != m2.getColNum()) {
        return false;
    }

    for (size_t i = 0; i < nrow; ++i) {
        for (size_t j = 0; j < ncol; ++j) {
            if (fabs(m1[i][j] - m2[i][j]) > 1e-5) { // double precison
                return false;
            }
        }
    }

    return true;
}

template <typename T>
inline ostream & operator<<(ostream & out, const matrix<T> & m)
{
    out << "[";
    for (size_t i = 0; i < m.getRowNum(); ++i) {
        out << (i == 0 ? "[" : " [");
        for (size_t j = 0; j < m.getColNum(); ++j) {
            out << (j == 0 ? "" : ", ");
            out << m[i][j];
        }
        out << (i != m.getRowNum() - 1 ? "],\n" : "]]\n");
     }

     return out;
}

#endif // _MATRIX_H_
