from django.test import TestCase
from django.contrib.auth import get_user_model

class UserTest(TestCase):
    def setUp(self):
        """
        There are two new instances of a User class created, and they both share the same password 
        and second password since there is no requirement for the system to set each distinct 
        password for each user.
        """
       
        # Load the custom User model
        self.user_model = get_user_model()
        
        # Create two users for testing
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

        return self.user_model.objects.create_user(
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

        user1 = self.user_model.objects.get(username="asdf1234")
        user2 = self.user_model.objects.get(username="asdf5678")

        assert isinstance(user1, self.user_model)
        assert user1.check_password("!ghdi35A93(02@+_2")
        assert user1.check_second_password("8Hd342!fh3@35")
        self.assertEqual("asdf345234", user1.get_nickname())
        self.assertEqual("example@example.com", user1.email)

        assert isinstance(user2, self.user_model)
        assert user2.check_password("!ghdi35A93(02@+_2")
        assert user2.check_second_password("8Hd342!fh3@35")
        self.assertEqual("asdf567867", user2.get_nickname())
        self.assertEqual("example1@example.com", user2.email)

    def test_change_User_nickname(self):
        """
        This test deals with trying to change the nickname of each user, and tests whether all the 
        requirements for changing one's nickname are met according to criteria
        """

        user1 = self.user_model.objects.get(username="asdf1234")
        user2 = self.user_model.objects.get(username="asdf5678")

        user1_old_nickname = "asdf345234"
        user2_old_nickname = "asdf567867"

        user1_new_nickname = "asdfv39847234"
        user2_new_nickname = "asdfv97458345"
        
        # Change their nicknames, and check whether it did go through successfully
        self.assertTrue(user1.set_nickname(user1_new_nickname))
        user1.save()

        self.assertFalse(user1.nickname == user1_old_nickname)
        self.assertTrue(user1.nickname == user1_new_nickname)

        self.assertTrue(user2.set_nickname(user2_new_nickname))
        user2.save()

        self.assertFalse(user2.nickname == user2_old_nickname)
        self.assertTrue(user2.nickname == user2_new_nickname)

        # Revert their nicknames back to their old ones
        self.assertTrue(user1.set_nickname(user1_old_nickname))
        user1.save()
        self.assertTrue(user1.nickname == user1_old_nickname)

        self.assertTrue(user2.set_nickname(user2_old_nickname))
        user2.save()
        self.assertTrue(user2.nickname == user2_old_nickname)


    def test_change_User_password(self):
        """
        This test deals with trying to change the password and second password of a user, and 
        verifying the change of the password and second password
        """

        user1 = self.user_model.objects.get(username="asdf1234")
        user2 = self.user_model.objects.get(username="asdf5678")
        
        # Both users share the same password and second password
        users_old_password = "!ghdi35A93(02@+_2"
        users_old_second_password = "8Hd342!fh3@35"

        users_new_password = "*6g#-gD348}{<245"
        users_new_second_password = "*6E1!344}{_(**&"
        
        # Change to new password and second password, and check whether they are successfully
        # changed
        user1.set_password(users_new_password)
        self.assertTrue(user1.set_second_password(users_new_second_password))
        self.assertTrue(user1.check_password(users_new_password))
        self.assertTrue(user1.check_second_password(users_new_second_password))

        user2.set_password(users_new_password)
        self.assertTrue(user2.set_second_password(users_new_second_password))
        self.assertTrue(user2.check_password(users_new_password))
        self.assertTrue(user2.check_second_password(users_new_second_password))
        
        # Set each user's password to something unusable, and check whether they are usable
        user1.set_unusable_password()
        user2.set_unusable_password()
        self.assertFalse(user1.has_usable_password())
        self.assertFalse(user2.has_usable_password())
        
        # Change each user's password back to their old one
        user1.set_password(users_old_password)
        user2.set_password(users_old_password)
        self.assertTrue(user1.check_password(users_old_password))
        self.assertTrue(user2.check_password(users_old_password))

        user1.save()
        user2.save()
