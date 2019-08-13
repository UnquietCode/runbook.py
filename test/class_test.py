from class_test_books import BookA, BookB


class BookC(BookB, BookA):
    
    def step_c4():
        pass


if __name__ == '__main__':
    BookC.main()