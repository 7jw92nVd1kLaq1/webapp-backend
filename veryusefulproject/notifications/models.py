from django.contrib.auth import get_user_model
from django.db import models

from uuid import uuid4

from .utils import MODEL_MAP, MODEL_UNIQUE_IDENTIFIER_FIELD_MAP

from veryusefulproject.core.models import BaseModel


User = get_user_model()


class EntityType(BaseModel):
    entity_name = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return "EntityType: {}".format(self.id)

    def get_entity_name(self):
        return self.entity_name


class NotificationAction(BaseModel):
    entity_type = models.ForeignKey(EntityType, on_delete=models.RESTRICT)
    action = models.CharField(max_length=256)
    code = models.CharField(max_length=128)
    desc = models.CharField(max_length=256)

    class Meta:
        unique_together = ['entity_type', 'action']

    def __str__(self):
        return "NotificationAction: {}".format(self.id)

    def get_code(self):
        return self.code

    def get_description(self):
        return self.desc

    def get_action(self):
        return self.action

    def get_entity_type(self):
        return self.entity_type.get_entity_name()

    def _check_placeholder_substring(self, placeholder_substring):
        """
        Returns a tuple of the role, name, and field of the model that the placeholder 
        substring will be replaced with.
        """

        if placeholder_substring.count(":") != 2:
            raise Exception("Invalid placeholder substring.")

        role = placeholder_substring[1:placeholder_substring.find(":")]
        name = placeholder_substring[
            placeholder_substring.find(":") + 1:placeholder_substring.rfind(":")]
        field = placeholder_substring[placeholder_substring.rfind(":") + 1:-1]

        if not role in ["actor", "affected", "involved"]:
            raise Exception("Invalid placeholder substring.")

        if len(name) == 0 or len(field) == 0:
            raise Exception("Invalid placeholder substring.")

        return role, name, field

    def parse_action_string(self):
        """
        Returns a list of dictionaries, where each dictionary contains the role, name,
        and field of the model that the placeholder substring will be replaced with.
        """

        temp_action_string_parsed_result = {"indexes": []}
        list_to_return = []

        action_string = self.get_action()

        for index, character in enumerate(action_string):
            if character == '{':
                temp_action_string_parsed_result["indexes"].append(index)
            elif character == '}':
                temp_action_string_parsed_result["indexes"].append(index)
                role, name, field = self._check_placeholder_substring(
                    action_string[
                        temp_action_string_parsed_result["indexes"][0]:temp_action_string_parsed_result["indexes"][1] + 1
                    ]
                )
                temp_action_string_parsed_result["role"] = role
                temp_action_string_parsed_result["name"] = name
                temp_action_string_parsed_result["field"] = field
                temp_action_string_parsed_result.pop("indexes")
                list_to_return.append(temp_action_string_parsed_result)
                temp_action_string_parsed_result = {"indexes": []}

        return list_to_return


class NotificationObject(BaseModel):
    action = models.ForeignKey(NotificationAction, on_delete=models.RESTRICT)
    
    def __str__(self):
        return "NotificationObject: {}".format(self.id)

    def stringify(self):
        """
        Returns a string representation of a notification.

        How does it work?
        1. Fetch the action object of a notification.
        2. Parse the "action" property of the action object by identifying all the 
        placeholder substrings (strings that start and end with curly braces) and seeing
        what models need to be queried, in order to compose a string representation of the 
        notification.
        3. Query the necessary models, and compose the string representation.
        4. Return the string representation.
        """
        
        replacement_strings = []

        actor_count = 0
        affected_count = 0
        involved_count = 0

        actor = self.get_actors()
        affected = self.get_affected_entities()
        involved = self.get_involved_entities()
        
        action = self.get_action()
        action_string = action.get_action()
        action_string_parsed_result = action.parse_action_string()
        for item in action_string_parsed_result:
            if item["role"] == "actor":
                actor = MODEL_MAP[item["name"]].objects.get(id=actor[actor_count].get_entity_id())
                value_for_replacement = getattr(actor, item["field"])
                replacement_strings.append(str(value_for_replacement))
                actor_count += 1

            elif item["role"] == "affected":
                affected = MODEL_MAP[item["name"]].objects.get(id=affected[affected_count].get_entity_id())
                value_for_replacement = getattr(affected, item["field"])
                replacement_strings.append(str(value_for_replacement))
                affected_count += 1

            elif item["role"] == "involved":
                involved = MODEL_MAP[item["name"]].objects.get(id=involved[involved_count].get_entity_id())
                value_for_replacement = getattr(involved, item["field"])
                replacement_strings.append(str(value_for_replacement))
                involved_count += 1
            else:
                raise Exception("Invalid role.")
        
        while action_string.find("{") != -1:
            action_string = action_string.replace(
                action_string[
                    action_string.find("{"):action_string.find("}") + 1
                ],
                replacement_strings.pop(0)
            )
       
        return action_string

    def return_affected_entities_unique_identifiers(self):
        """
        Returns a list of unique identifiers of the affected entities of a notification.
        """

        result = []
        affected_entities = self.get_affected_entities()

        for affected_entity in affected_entities:
            entity_name = affected_entity.get_entity_type()
            field = MODEL_UNIQUE_IDENTIFIER_FIELD_MAP[entity_name]
            affected = MODEL_MAP[entity_name].objects.get(
                id=affected_entity.get_entity_id()
            )
            affected_identity_unique_identifier = getattr(affected, field)
            result.append(affected_identity_unique_identifier)

        return result

    def get_action(self):
        return self.action

    def get_actors(self):
        return self.notificationobjectactor_set.all()

    def get_affected_entities(self):
        return self.notificationobjectaffectedentity_set.all()

    def get_involved_entities(self):
        return self.notificationobjectinvolvedentity_set.all()

    def add_actor(self, entity_type, entity_id):
        if not MODEL_MAP.get(entity_type, None):
            raise Exception("Invalid entity type.")
        
        entity_does_exist = MODEL_MAP[entity_type].objects.filter(id=entity_id).exists()
        if not entity_does_exist:
            raise Exception("Invalid entity id.")

        return NotificationObjectActor.objects.create(
            notification_object=self,
            entity_type=EntityType.objects.get(entity_name=entity_type),
            entity_id=entity_id
        )

    def add_affected_entity(self, entity_type, entity_id):
        if not MODEL_MAP.get(entity_type, None):
            raise Exception("Invalid entity type.")
        
        entity_does_exist = MODEL_MAP[entity_type].objects.filter(id=entity_id).exists()
        if not entity_does_exist:
            raise Exception("Invalid entity id.")

        return NotificationObjectAffectedEntity.objects.create(
            notification_object=self,
            entity_type=EntityType.objects.get(entity_name=entity_type),
            entity_id=entity_id
        )

    def add_involved_entity(self, entity_type, entity_id):
        if not MODEL_MAP.get(entity_type, None):
            raise Exception("Invalid entity type.")
        
        entity_does_exist = MODEL_MAP[entity_type].objects.filter(id=entity_id).exists()
        if not entity_does_exist:
            raise Exception("Invalid entity id.")

        return NotificationObjectInvolvedEntity.objects.create(
            notification_object=self,
            entity_type=EntityType.objects.get(entity_name=entity_type),
            entity_id=entity_id
        )


class NotificationObjectActor(BaseModel):
    notification_object = models.ForeignKey(
        NotificationObject, on_delete=models.RESTRICT)
    entity_type = models.ForeignKey(EntityType, on_delete=models.RESTRICT)
    entity_id = models.CharField(max_length=128)

    class Meta:
        unique_together = ['notification_object', 'entity_type', 'entity_id']

    def set_entity_type(self, entity_type):
        try:
            self.entity_type = EntityType.objects.get(entity_name=entity_type)
        except EntityType.DoesNotExist:
            raise Exception("Invalid entity type.")

        self.save(update_fields=['entity_type'])

    def set_entity_id(self, entity_id):
        if not MODEL_MAP.get(self.get_entity_type(), None):
            raise Exception("Invalid entity type.")
        
        try:
            MODEL_MAP[self.get_entity_type()].objects.get(id=entity_id)
        except MODEL_MAP[self.get_entity_type()].DoesNotExist:
            raise Exception("Invalid entity id.")
        except KeyError:
            raise Exception("Invalid entity type.")

        self.entity_id = entity_id
        self.save(update_fields=['entity_id'])

    def get_entity_id(self):
        return self.entity_id

    def get_entity_type(self):
        return self.entity_type.get_entity_name()


class NotificationObjectAffectedEntity(BaseModel):
    notification_object = models.ForeignKey(
        NotificationObject, on_delete=models.RESTRICT)
    entity_type = models.ForeignKey(EntityType, on_delete=models.RESTRICT)
    entity_id = models.CharField(max_length=128)

    class Meta:
        unique_together = ['notification_object', 'entity_type', 'entity_id']

    def set_entity_type(self, entity_type):
        try:
            self.entity_type = EntityType.objects.get(entity_name=entity_type)
        except EntityType.DoesNotExist:
            raise Exception("Invalid entity type.")

        self.save(update_fields=['entity_type'])

    def set_entity_id(self, entity_id):
        if not MODEL_MAP.get(self.get_entity_type(), None):
            raise Exception("Invalid entity type.")
        
        try:
            MODEL_MAP[self.get_entity_type()].objects.get(id=entity_id)
        except MODEL_MAP[self.get_entity_type()].DoesNotExist:
            raise Exception("Invalid entity id.")
        except KeyError:
            raise Exception("Invalid entity type.")

        self.entity_id = entity_id
        self.save(update_fields=['entity_id'])

    def get_entity_id(self):
        return self.entity_id

    def get_entity_type(self):
        return self.entity_type.get_entity_name()


class NotificationObjectInvolvedEntity(BaseModel):
    notification_object = models.ForeignKey(
        NotificationObject, on_delete=models.RESTRICT)
    entity_type = models.ForeignKey(EntityType, on_delete=models.RESTRICT)
    entity_id = models.CharField(max_length=128)

    class Meta:
        unique_together = ['notification_object', 'entity_type', 'entity_id']

    def set_entity_type(self, entity_type):
        try:
            self.entity_type = EntityType.objects.get(entity_name=entity_type)
        except EntityType.DoesNotExist:
            raise Exception("Invalid entity type.")

        self.save(update_fields=['entity_type'])

    def set_entity_id(self, entity_id):
        if not MODEL_MAP.get(self.get_entity_type(), None):
            raise Exception("Invalid entity type.")
        
        try:
            MODEL_MAP[self.get_entity_type()].objects.get(id=entity_id)
        except MODEL_MAP[self.get_entity_type()].DoesNotExist:
            raise Exception("Invalid entity id.")
        except KeyError:
            raise Exception("Invalid entity type.")

        self.entity_id = entity_id
        self.save(update_fields=['entity_id'])

    def get_entity_id(self):
        return self.entity_id

    def get_entity_type(self):
        return self.entity_type.get_entity_name()


class Notification(BaseModel):
    identifier = models.UUIDField(default=uuid4)
    notifiers = models.ManyToManyField(
        User, 
        related_name="notification_as_notifiers"
    )
    notification_object = models.ForeignKey(
        NotificationObject, 
        on_delete=models.RESTRICT
    )
    read = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['identifier']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return "Notification: {}".format(self.id)

    def get_notifiers(self):
        return self.notifiers.all()

    def add_notifier(self, user):
        self.notifiers.add(user)

    def remove_notifier(self, user):
        self.notifiers.remove(user)

    def toggle_read(self):
        self.read = not self.read
        self.save(update_fields=['read'])
