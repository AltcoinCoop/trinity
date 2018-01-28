from sqlalchemy import Column, String, create_engine, Integer, Float, BigInteger, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from configure import Configure
from exception import ChannelDBAddFail, ChannelDBUpdateFail, ChannelExist, QureyRoleNotCorrect
import json

Base = declarative_base()

DATABASE_PAHT = Configure["DBFile"]


class ChannelAddrDataBase(Base):
    """
    channel address table

    """
    __tablename__ = 'channel address database'

    address = Column(String(256), primary_key=True)
    ip = Column(String())
    port = Column(String())
    public_key = Column(String())


class ChannelAddress(object):
    """
    channel address managment
    """

    def __init__(self):
        pass

    def add_address(self, address, ip="NULL", port="NULL", public_key="NULL"):
        try:
            if self.query_address(address):
                print("query_address get %s" %address)
                Session.merge(ChannelAddrDataBase(address=address, ip=ip, port=port, public_key= public_key))
            else:
                Session.add(ChannelAddrDataBase(address=address, ip=ip, port=port, public_key= public_key))
            Session.commit()
        except:
            raise ChannelDBAddFail
        return None

    def delete_address(self, address):
        try:
            Session.query(ChannelAddrDataBase).filter(ChannelAddrDataBase.address == address).delete()
            Session.commit()
        except:
            raise
        return None

    def query_address(self, address):
        try:
            result = Session.query(ChannelAddrDataBase).filter(ChannelAddrDataBase.address == address).one()
        except:
            return None
        return result

    def update_address(self, address, ip, port, public_key="NULL"):
        try:
            Session.merge(ChannelAddrDataBase(address=address, ip=ip, port=port, public_key= public_key))
            Session.commit()
        except:
            raise ChannelDBUpdateFail
        return None


class ChannelDatabase(Base):
    """
    channel table
    """
    __tablename__ = 'channel database'

    channel_name = Column(String(256), primary_key=True)
    receiver = Column(String(256))
    sender =  Column(String(256))
    state = Column(Integer())
    sender_deposit = Column(Float())
    receiver_deposit = Column(Float())
    open_block_number = Column(Integer())
    start_block_number = Column(BigInteger())
    settle_timeout = Column(Integer())
    sender_deposit_cache = Column(Float())
    receiver_deposit_cache = Column(Float())
    tx_info = Column(Text())


engine = create_engine('sqlite:///'+DATABASE_PAHT)
DBSession = sessionmaker(bind=engine)
Session = DBSession()
Base.metadata.create_all(engine)


class ChannelState(object):
    """
    Channel state
    """
    def __init__(self, channelname):
        self.match = None
        self.channelname= channelname
        self.find_channel()

    def find_channel(self):
        try:
            self.match = Session.query(ChannelDatabase).filter(ChannelDatabase.channel_name == self.channelname).one()
            return True if self.match else False
        except:
            return False

    @property
    def stateinDB(self):
        return self.match.state

    @property
    def senderinDB(self):
        return self.match.sender

    @property
    def recieverinDB(self):
        return self.match.receiver

    @property
    def receiver_deposit(self):
        return self.match.receiver_deposit

    @property
    def sender_deposit_cache(self):
        return self.match.sender_deposit_cache

    @property
    def receiver_deposit_cache(self):
        return self.match.receiver_deposit_cache

    @property
    def sender_deposit(self):
        return self.match.sender_deposit

    @property
    def receiver_in_database(self):
        return self.match.receiver if self.match else None
        
    @property
    def state_in_database(self):
        return self.match.state if self.match else None

    @property
    def open_block_number(self):
        return self.match.open_block_number

    def add_channle_to_database(self, sender, receiver, channel_name, state, sender_deposit,receiver_deposit,
                                open_block_number, settle_timeout, sender_deposit_cache, receiver_deposit_cache,
                                start_block_number = 0):
        channel_state = ChannelDatabase(receiver=receiver, sender= sender, channel_name=channel_name, state=state.value,
                                        sender_deposit=sender_deposit,receiver_deposit = receiver_deposit,
                                        open_block_number=open_block_number, settle_timeout = settle_timeout,
                                        sender_deposit_cache=sender_deposit_cache,
                                        receiver_deposit_cache=receiver_deposit_cache,
                                        start_block_number=start_block_number, tx_info = "")
        try:
            Session.add(channel_state)
            Session.commit()
        except:
            raise ChannelDBAddFail
        return None

    def update_channel_to_database(self,**kwargs):
        self.find_channel()
        try:
            for key, value in kwargs.items():
                setattr(self.match, key,value)
            Session.commit()
        except:
            raise ChannelDBUpdateFail
        return None

    def update_channel_state(self, state):
        ch = Session.query(ChannelDatabase).filter(ChannelDatabase.channel_name == self.channelname).one()
        if ch:
            ch.state = state.value
            Session.commit()
            return True
        else:
            return False
        #return self.update_channel_to_database(state=state.value)

    def update_deposit_cache(self,sender_deposit_cache, receiver_deposit_cache):
        ch = Session.query(ChannelDatabase).filter(ChannelDatabase.channel_name == self.channelname).one()
        if ch:
            ch.sender_deposit_cache = sender_deposit_cache
            ch.receiver_deposit_cache = receiver_deposit_cache
            Session.commit()
            return True
        else:
            return False

    def update_channel_deposit(self, sender_deposit, receiver_deposit):
        ch = Session.query(ChannelDatabase).filter(ChannelDatabase.channel_name == self.channelname).one()
        if ch:
            ch.sender_deposit = sender_deposit
            ch.receiver_deposit = receiver_deposit
            Session.commit()
            return True
        else:
            return False

    def delete_channle_in_database(self):
        try:
            Session.query(ChannelDatabase).filter(ChannelDatabase.channel_name == self.channelname).delete()
            Session.commit()
        except:
            raise
        return None

    def create_channelfile(self, **kwargs):
        json_str = json.dumps(kwargs)
        ch = Session.query(ChannelDatabase).filter(ChannelDatabase.channel_name == self.channelname).one()
        if ch:
            ch.tx_info = json_str
            Session.commit()
            return True
        else:
            return False


    def update_channel(self, **kwargs):
        ch = Session.query(ChannelDatabase).filter(ChannelDatabase.channel_name == self.channelname).one()
        if ch:
            info = ch.tx_info
            json_str = json.dumps(kwargs)
            info = info+"#"*10+json_str
            ch.tx_info = info
            Session.commit()
            return True
        else:
            return False


    def read_channel(self):
        ch = Session.query(ChannelDatabase).filter(ChannelDatabase.channel_name == self.channelname).one()
        if ch:
            info = ch.tx_info
            info_list = info.split("#"*10)
            return [json.loads(i) for i in info_list]
        else:
            return False


    def has_channel_file(self):
        ch = Session.query(ChannelDatabase).filter(ChannelDatabase.channel_name == self.channelname).one()
        return True if ch else False


def query_channel_from_address(address, role="both"):
    if role not in ("both", "sender", "receiver"):
        raise QureyRoleNotCorrect
    if role == "sender":
        return Session.query(ChannelDatabase).filter(ChannelDatabase.sender == address).all()
    elif role == "receiver":
        return  Session.query(ChannelDatabase).filter(ChannelDatabase.receiver == address).all()
    else:
        result = Session.query(ChannelDatabase).filter(ChannelDatabase.sender == address).all()
        result.extend(Session.query(ChannelDatabase).filter(ChannelDatabase.receiver == address).all())
        return result


if __name__ == "__main__":
    from channel_manager.channel import State
    channel =  ChannelAddress()
    #channel.add_channle_to_database(sender="test_sender", sender_deposit=10, receiver="test_receiver", receiver_deposit=20, channel_name="testchannlenametest",
     #                               open_block_number=1000, settle_timeout=100, state=State.OPENING)
    #channel.add_channle_to_database(sender="test_sender", sender_deposit=10, receiver="test_receiver",
      #                              receiver_deposit=20, channel_name="testchannelname",
     #                               open_block_number=1000, settle_timeout=100, state=State.OPENING)
    result = channel.add_address("test_sender1dt11","10.10.101.01")
    print(result)







