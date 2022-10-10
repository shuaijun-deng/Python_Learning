"""
1. 设计模式与面向对象
(1) 接口: 若干抽象方法的集合
    作用: 限制实现接口的类必须按照接口给定的调用方式实现这些方法,对高层模块隐藏了类内部的实现

2. 面向对象设计的SOLID原则
(1) 开放封闭原则: 一个软件实体如类,模块和函数应该对扩展开放,对修改封闭.(也就是软件实例应该在尽量不修改原有代码的情况下进行扩展)
(2) 里氏替换原则: 所有引用父类的地方必须能够透明的引用子类的对象
(3) 依赖倒置原则: 高层模块不应该依赖底层模块,二则都应该依赖其抽象,抽象不应该依赖细节,细节应该依赖抽象,也就是说要针对接口编程而不是针对实现编程.
(4) 接口隔离原则: 使用多个专门的接口,而不是使用单一的总接口, 也就是客户端不应该依赖那些他不需要的接口
(5) 单一职责原则: 不要存在多于一个导致类变更的原因,通俗的说就是一个类只负责一项职责
"""

# 接口隔离原则
from abc import ABCMeta


class Animal(metaclass=ABCMeta):
    def work(self):
        pass

    def swim(self):
        pass

    def fly(self):
        pass


# --------------------------------------创建型模式--------------------------------------
"""
创建型模式:
(1) 简单工厂模式
内容: 不直接向客户端暴露对象创建的实现细节,而是通过一个工厂类来负责创建产品类的实例
角色: (1) 工厂角色(Creator) (2) 抽象产品角色(Product) (3) 具体产品角色(Concrete Product)
优点: (1) 隐藏了对象创建的实现细节 (2) 客户端不需要修改代码
缺点: (1) 违反了单一职责原则,将创建逻辑集中到一个工厂类里面 (2) 当添加新产品时,需要修改工厂类代码,违反了开闭原则
"""
from abc import ABCMeta, abstractmethod


class Payment(metaclass=ABCMeta):
    """
    使用抽象类定义接口, 在简单工厂模式中相当于抽象产品的角色
    """

    @abstractmethod
    def pay(self, money):
        pass


# 基于抽象方法创建两个具体的类AliPay和WechatPay实现各自的支付方法,在简单工厂模式中相当于具体产品的角色
class AliPay(Payment):
    def pay(self, money):
        print(f"支付宝支付{money}元.")


class WechatPay(Payment):
    def pay(self, money):
        print(f"微信支付{money}元")


# 创建一个工厂类用来负责创建产品类的实例,在简单工厂模式中相当于工厂角色
class PaymentFactory:
    def create_payment(self, method):
        if method == "alipay":
            return AliPay()
        elif method == "wechat":
            return WechatPay()
        else:
            raise TypeError(f"No such payment named {method}")


# client
pf = PaymentFactory()
p = pf.create_payment("alipay")
p.pay(100)

"""
(2) 工厂方法模式
内容: 定义一个创建对象的接口(工厂接口), 让子类决定实例化哪一类产品类
角色: (1) 抽象工厂角色 (2) 具体工厂角色 (3) 抽象产品角色 (4) 具体产品角色
优点: (1) 每个产品都对应一个具体的工厂类,不需要修改工厂类代码 (2) 隐藏了对象创建的实现细节
缺点: 每增加一个具体的产品类就必须增加一个相应的具体工厂类
"""
from abc import ABCMeta, abstractmethod


# 使用抽象类定义接口, 在工厂模式中相当于抽象产品的角色
class Payment(metaclass=ABCMeta):
    @abstractmethod
    def pay(self, money):
        pass


# 基于抽象方法创建两个具体的类AliPay和WechatPay实现各自的支付方法,在工厂模式中相当于具体产品的角色
class AliPay(Payment):
    def pay(self, money):
        print(f"支付宝支付{money}元.")


class WechatPay(Payment):
    def pay(self, money):
        print(f"微信支付{money}元")


# 创建一个工厂接口, 在工厂模式中相当于抽象工厂的角色
class PaymentFactory(metaclass=ABCMeta):
    @abstractmethod
    def create_payment(self):
        pass


# 创建两个具体工厂类, 在工厂模式中充当具体工厂的角色
class AliPayFactory(PaymentFactory):
    def create_payment(self):
        return AliPay()


class WechatPayFactory(PaymentFactory):
    def create_payment(self):
        return WechatPay()


"""
(3) 抽象工厂模式
内容: 定义一个工厂类接口,让工厂类来创建一系列相关或者相互依赖的对象,相比工厂方法模式,抽象工厂模式中每个具体工厂都生产一套产品
角色: (1) 抽象工厂角色 (2) 具体工厂角色 (3) 抽象产品角色 (4) 具体产品角色
优点: (1) 将客户端与类的具体实现相分离 (2) 每个工厂创建了一个完整的产品系列,使得易于交换产品系列 (3)有利于产品的一致性(也就是产品之间的约束关系)
缺点: 难以支持新种类的(抽象)产品
"""
from abc import abstractmethod, ABCMeta


# -----抽象产品-----
class PhoneShell(metaclass=ABCMeta):
    @abstractmethod
    def show_shell(self):
        pass


class CPU(metaclass=ABCMeta):
    @abstractmethod
    def show_cpu(self):
        pass


class OS(metaclass=ABCMeta):
    @abstractmethod
    def show_os(self):
        pass


# ----抽象工厂-----
class PhoneFactory(metaclass=ABCMeta):
    @abstractmethod
    def make_shell(self):
        pass

    @abstractmethod
    def make_cpu(self):
        pass

    @abstractmethod
    def make_os(self):
        pass


# -----具体产品-----
class SmallShell(PhoneShell):
    def show_shell(self):
        print("普通手机小手机壳")


class BigShell(PhoneShell):
    def show_shell(self):
        print("普通手机大手机壳")


class AppleShell(PhoneShell):
    def show_shell(self):
        print("苹果手机壳")


class SnapDragonCPU(CPU):
    def show_cpu(self):
        print("骁龙CPU")


class MediaTekCPU(CPU):
    def show_cpu(self):
        print("联发科CPU")


class AppleCPU(CPU):
    def show_cpu(self):
        print("苹果CPU")


class Android(OS):
    def show_os(self):
        print("Android操作系统")


class IOS(OS):
    def show_os(self):
        print("IOS操作系统")


# -----具体工厂-----
class MiFactory(PhoneFactory):
    def make_cpu(self):
        return SnapDragonCPU()

    def make_os(self):
        return Android()

    def make_shell(self):
        return SmallShell()


class AppleFactory(PhoneFactory):
    def make_cpu(self):
        return AppleCPU()

    def make_os(self):
        return IOS()

    def make_shell(self):
        return AppleShell()


# -----客户端-----
class Phone:
    def __init__(self, cpu, os, shell):
        self.cpu = cpu
        self.os = os
        self.shell = shell

    def show_info(self):
        print("手机信息:")
        self.cpu.show_cpu()
        self.os.show_os()
        self.shell.show_shell()


def make_phone(factory):
    cpu = factory.make_cpu()
    os = factory.make_os()
    shell = factory.make_shell()
    return Phone(cpu, os, shell)


p1 = make_phone(MiFactory())
p1.show_info()

"""
(4) 建造者模式
内容: 将一个复杂对象的构建与它的表示分离,使得同样的构建过程可以创建不同的表示(建造者模式与抽象工厂模式相似,也用来撞见复杂的对象,
     主要区别是建造者模式是一步步构建一个复杂的对象,而抽象工厂模式是多个系列产品对象)
角色: (1) 抽象建造者(Builder) (2) 具体建造者(Concrete Builder) (3) 指挥者(Director) (4) 产品(Product)
优点: (1) 隐藏了一个产品的内部结构和装配过程 (2) 将构造代码与表示代码分开 (3) 可以对构造过程进行更加精细的控制
缺点: 
"""
from abc import ABCMeta, abstractmethod


class Player:
    def __init__(self, face=None, body=None, arm=None, leg=None):
        self.face = face
        self.body = body
        self.arm = arm
        self.leg = leg

    def __str__(self):
        return f"{self.face}, {self.body}, {self.arm}, {self.leg}"


class PlayerBuilder(metaclass=ABCMeta):
    @abstractmethod
    def build_face(self):
        pass

    @abstractmethod
    def build_body(self):
        pass

    @abstractmethod
    def build_arm(self):
        pass

    @abstractmethod
    def build_leg(self):
        pass


class SexyGirlBuilder(PlayerBuilder):
    def __init__(self):
        self.player = Player()

    def build_face(self):
        self.player.face = "漂亮脸蛋"

    def build_body(self):
        self.player.body = "苗条"

    def build_arm(self):
        self.player.arm = "洁白如玉藕的胳膊"

    def build_leg(self):
        self.player.leg = "大长腿"


class MonsterBuilder(PlayerBuilder):
    def __init__(self):
        self.player = Player()

    def build_face(self):
        self.player.face = "怪兽脸"

    def build_body(self):
        self.player.body = "巨大"

    def build_arm(self):
        self.player.arm = "长毛的胳膊"

    def build_leg(self):
        self.player.leg = "巨大的腿"


# 控制组装的顺序
class PlayerDirector():
    def build_player(self, builder):
        builder.build_body()
        builder.build_face()
        builder.build_arm()
        builder.build_leg()
        return builder.player


# -----client-----
builder = SexyGirlBuilder()
director = PlayerDirector()
p = director.build_player(builder)
print(p)

"""
(5) 单例模式
内容: 保证一个类只有一个实例,并提供一个访问它的全局访问点
角色: 单例(Singleton)
优点: (1) 对唯一实例的受控访问 (2) 单例相当于全局变量,但是防止命名空间被污染
"""
from abc import abstractmethod, ABCMeta


class Singleton()
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._intance = super(Singleton, cls).__new__(cls)
        return cls._intance


class MyClass(Singleton):
    def __init__(self, a):
        self.a = a


a = MyClass(10)
b = MyClass(20)

print(a.a)
print(b.a)
print(id(a), id(b))

# --------------------------------------结构型模式--------------------------------------
"""
(1) 适配器模式
定义: 将一个类的接口转换成客户希望的另一个接口,适配器模式使得原本由于接口不兼容而不能一起工作的哪些类可以一起工作
实现方式: (1) 类适配器(基于多继承) (2) 对象适配器(基于组合)
"""
from abc import ABCMeta, abstractmethod


class Payment(metaclass=ABCMeta):
    @abstractmethod
    def pay(self, money):
        pass


class AliPay(Payment):
    def pay(self, money):
        print(f"支付宝支付{money}元.")


class WechatPay(Payment):
    def pay(self, money):
        print(f"微信支付{money}元")


class BankPay():
    def cost(self, money):
        print(f"银联支付{money}元")


class ApplePay():
    def cost(self, money):
        print(f"苹果支付{money}元")


# 类适配器类
# class NewBankPay(Payment, BankPay):
#     def pay(self, money):
#         self.cost(money)

# 对象适配器
class PaymentAdapter(Payment):
    def __init__(self, payment):
        self.payment = payment

    def pay(self, money):
        self.payment.cost(money)


p = NewBankPay()
p.pay(100)


# 组合: 在一个类中放入另一个类对象
class A()
    pass


class B:
    def __init__(self):
        self.a = A()


"""
(2) 桥模式
定义: 将一个事物的两个维度分离,使其都可以独立的变化
角色: (1) 抽象(Abstraction) (2) 细化抽象(RefinedAbstraction) (3) 实现者(Implementor) (4) 具体实现者(ConcreteImplementor)
应用场景: 当事物有两个维度的表现, 两个维度都可能扩展时
优点: (1) 抽象和实现相分离 (2) 优秀的扩展能力
"""
from abc import ABCMeta, abstractmethod


class Shape(metaclass=ABCMeta):
    def __init__(self, color):
        self.color = color

    @abstractmethod
    def draw(self):
        pass


class Color(metaclass=ABCMeta):
    @abstractmethod
    def paint(self, shape):
        pass


class Rectangle(Shape):
    name = "长方形"
    def draw(self):
        self.color.paint(self)


class Circle(Shape):
    name = "圆形"
    def draw(self):
        self.color.paint(self)

class Red(Color):
    def paint(self, shape):
        print(f"红色的{shape.name}")

class Green(color):
    def paint(self, shape):
        print(f"绿色的{shape.name}")

shape = Retangle(Red())
shape.draw()

shape2 = Circle(Green())
shape2.draw()


"""
(3) 组合模式
定义: 将对象组合层树形结构以表示'部分-整体'的层次结构,组合模式使得用户对单个对象和组合对象的使用具有一致性
角色: (1) 抽象组件(Component) (2) 叶子组件(Leaf) (3) 复合组件(Composite) (4) 客户端(Client)
应用场景: 当事物有两个维度的表现, 两个维度都可能扩展时
优点: (1) 抽象和实现相分离 (2) 优秀的扩展能力
"""