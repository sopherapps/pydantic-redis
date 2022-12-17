"""Tests for benchmarks"""
import pytest

from test.conftest import (
    redis_store_fixture,
    Book,
    books,
    books_fixture,
    update_books_fixture,
    delete_books_fixture,
)


@pytest.mark.parametrize("store", redis_store_fixture)
def test_benchmark_bulk_insert(benchmark, store):
    """Benchmarks the bulk_insert operation"""
    benchmark(Book.insert, books)


@pytest.mark.parametrize("store, book", books_fixture)
def test_benchmark_single_insert(benchmark, store, book):
    """Benchmarks the single insert operation"""
    benchmark(Book.insert, book)


@pytest.mark.parametrize("store", redis_store_fixture)
def test_benchmark_select_default(benchmark, store):
    """Benchmarks the select default operation"""
    Book.insert(books)
    benchmark(Book.select)


@pytest.mark.parametrize("store", redis_store_fixture)
def test_benchmark_select_default_paginated(benchmark, store):
    """Benchmarks the select default operation when paginated"""
    Book.insert(books)
    benchmark(Book.select, skip=2, limit=2)


@pytest.mark.parametrize("store", redis_store_fixture)
def test_benchmark_select_columns(benchmark, store):
    """Benchmarks the select columns operation"""
    Book.insert(books)
    benchmark(Book.select, columns=["title", "author", "in_stock"])


@pytest.mark.parametrize("store", redis_store_fixture)
def test_benchmark_select_columns_paginated(benchmark, store):
    """Benchmarks the select columns operation, when paginated"""
    Book.insert(books)
    benchmark(Book.select, columns=["title", "author", "in_stock"], skip=2, limit=2)


@pytest.mark.parametrize("store", redis_store_fixture)
def test_benchmark_select_some_items(benchmark, store):
    """Benchmarks the select some items operation"""
    Book.insert(books)
    ids = [book.title for book in books[:2]]
    benchmark(Book.select, ids=ids)


@pytest.mark.parametrize("store", redis_store_fixture)
def test_benchmark_select_columns_for_some_items(benchmark, store):
    """Benchmarks the select columns for some items only operation"""
    Book.insert(books)
    ids = [book.title for book in books[:2]]
    benchmark(Book.select, columns=["title", "author", "in_stock"], ids=ids)


@pytest.mark.parametrize("store, book", books_fixture)
def test_benchmark_select_columns_for_one_id(benchmark, store, book):
    """Benchmarks the select columns for one id operation"""
    Book.insert(books)
    benchmark(Book.select, columns=["title", "author", "in_stock"], ids=[book.title])


@pytest.mark.parametrize("store, book", books_fixture)
def test_benchmark_select_all_for_one_id(benchmark, store, book):
    """Benchmarks the select all columns for one id operation"""
    Book.insert(books)
    benchmark(Book.select, ids=[book.title])


@pytest.mark.parametrize("store, title, data", update_books_fixture)
def test_benchmark_update(benchmark, store, title, data):
    """Benchmarks the update operation"""
    Book.insert(books)
    benchmark(Book.update, title, data=data)


@pytest.mark.parametrize("store, title", delete_books_fixture)
def test_benchmark_delete(benchmark, store, title):
    """Benchmarks the delete operation"""
    Book.insert(books)
    benchmark(Book.delete, [title])


@pytest.mark.parametrize("store", redis_store_fixture)
def test_benchmark_bulk_delete(benchmark, store):
    """Benchmarks the bulk delete operation"""
    Book.insert(books)
    benchmark(Book.delete, [book.title for book in books])
