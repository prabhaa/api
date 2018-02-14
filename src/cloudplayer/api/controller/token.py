"""
    cloudplayer.api.controller.token
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2018 by Nicolas Drebenstedt
    :license: GPL-3.0, see LICENSE for details
"""
import datetime

import tornado.gen
import tornado.options as opt

from cloudplayer.api.controller import Controller, ControllerException
from cloudplayer.api.model.token import Token


class TokenController(Controller):

    __model__ = Token

    @tornado.gen.coroutine
    def create(self, ids, **kw):
        entity = yield super().create({})
        return entity

    @tornado.gen.coroutine
    def read(self, ids):
        threshold = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
        query = self.db.query(
            self.__model__).filter_by(**ids).filter(Token.created > threshold)
        entity = query.one_or_none()
        if not entity:
            raise ControllerException(404)
        account = self.accounts.get(entity.provider_id)
        self.policy.grant_read(account, entity)
        if entity.claimed:
            self.current_user['user_id'] = entity.account.user_id
            for p in opt.options['providers']:
                self.current_user[p] = None
            for a in entity.account.user.accounts:
                self.current_user[a.provider_id] = a.id
            entity.account_id = None
            entity.account_provider_id = None
            self.db.commit()
        return entity

    @tornado.gen.coroutine
    def update(self, ids, **kw):
        entity = yield super().update(
            ids,
            claimed=True,
            account_id=self.current_user['cloudplayer'],
            account_provider_id='cloudplayer')
        return entity
