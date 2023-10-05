from django.test import TestCase
from django.contrib.auth import get_user_model


User = get_user_model()

class UserTest(TestCase):
    def setUp(self):
        """
        There are two new instances of a User class created, and they both share the same password 
        and second password since there is no requirement for the system to set each distinct 
        password for each user.
        """

        user1_username = "asdf1234"
        user1_password = "!ghdi35A93(02@+_2"
        user1_second_password = "8Hd342!fh3@35"
        user1_nickname = "asdf345234"
        user1_email = "example@example.com"

        user2_username = "asdf5678"
        user2_password = "!ghdi35A93(02@+_2"
        user2_second_password = "8Hd342!fh3@35"
        user2_nickname = "asdf567867"
        user2_email = "example1@example.com"

        self.createUser(
            user1_username,
            user1_password,
            user1_second_password,
            user1_nickname,
            user1_email
        )

        self.createUser(
            user2_username,
            user2_password,
            user2_second_password,
            user2_nickname,
            user2_email
        )

    def createUser(self, username, password, second_password, nickname, email):
        """
        A helper function for creating a new instance of a User class
        """

        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
            second_password=second_password,
            nickname=nickname
        )

    def test_User_data_integrity(self):
        """
        This directly deals with the integrity of data of each user created, to ensure that each
        user is registered with the exact information provided at the time of its creation.
        """

        user1 = User.objects.get(username="asdf1234")
        user2 = User.objects.get(username="asdf5678")

        assert self.assertTrue(isinstance(user1, User))
        assert self.assertTrue(user1.check_password("!ghdi35A93(02@+_2"))
        assert self.assertTrue(user1.check_second_password("8Hd342!fh3@35"))
        assert self.assertEqual("asdf345234", user1.get_nickname())
        assert self.assertEqual("example@example.com", user1.email)

        assert self.assertTrue(isinstance(user2, User))
        assert self.assertTrue(user2.check_password("!ghdi35A93(02@+_2"))
        assert self.assertTrue(user2.check_second_password("8Hd342!fh3@35"))
        assert self.assertEqual("asdf567867", user2.get_nickname())
        assert self.assertEqual("example1@example.com", user2.email)
