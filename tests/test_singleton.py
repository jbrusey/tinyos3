import unittest
from tinyos3.utils.Singleton import Singleton, SingletonException, MetaSingleton


class PublicInterfaceTest(unittest.TestCase):
    def testReturnsSameObject(self):
        """Demonstrates normal use -- just call getInstance and it
        returns a singleton instance

        """

        class A(Singleton):
            def __init__(self):
                super(A, self).__init__()

        a1 = A.getInstance()
        a2 = A.getInstance()
        self.assertEqual(id(a1), id(a2))

    def testInstantiateWithMultiArgConstructor(self):
        """
        If the singleton needs args to construct, include them in the first
        call to get instances.
        """

        class B(Singleton):
            def __init__(self, arg1, arg2):
                super(B, self).__init__()
                self.arg1 = arg1
                self.arg2 = arg2

        b1 = B.getInstance("arg1 value", "arg2 value")
        b2 = B.getInstance()
        self.assertEqual(b1.arg1, "arg1 value")
        self.assertEqual(b1.arg2, "arg2 value")
        self.assertEqual(id(b1), id(b2))

    def testTryToInstantiateWithoutNeededArgs(self):
        class B(Singleton):
            def __init__(self, arg1, arg2):
                super(B, self).__init__()
                self.arg1 = arg1
                self.arg2 = arg2

        self.assertRaises(SingletonException, B.getInstance)

    def testTryToInstantiateWithoutGetInstance(self):
        """Demonstrates that singletons can ONLY be instantiated
        through getInstance, as long as they call Singleton.__init__
        during construction.

        If this check is not required, you don't need to call
        Singleton.__init__().

        """

        class A(Singleton):
            def __init__(self):
                super(A, self).__init__()

        self.assertRaises(SingletonException, A)

    def testDontAllowNew(self):
        def instantiatedAnIllegalClass():
            class A(Singleton):
                def __init__(self):
                    super(A, self).__init__()

                def __new__(metaclass, strName, tupBases, dict):
                    return super(MetaSingleton, metaclass).__new__(
                        metaclass, strName, tupBases, dict
                    )

        self.assertRaises(SingletonException, instantiatedAnIllegalClass)

    def testDontAllowArgsAfterConstruction(self):
        class B(Singleton):
            def __init__(self, arg1, arg2):
                super(B, self).__init__()
                self.arg1 = arg1
                self.arg2 = arg2

        _ = B.getInstance("arg1 value", "arg2 value")
        self.assertRaises(SingletonException, B, "arg1 value", "arg2 value")

    def test_forgetClassInstanceReferenceForTesting(self):
        class A(Singleton):
            def __init__(self):
                super(A, self).__init__()

        class B(A):
            def __init__(self):
                super(B, self).__init__()

        # check that changing the class after forgetting the instance produces
        # an instance of the new class
        a = A.getInstance()
        assert a.__class__.__name__ == "A"
        A._forgetClassInstanceReferenceForTesting()
        b = B.getInstance()
        assert b.__class__.__name__ == "B"

        # check that invoking the 'forget' on a subclass still deletes
        # the instance
        B._forgetClassInstanceReferenceForTesting()
        a = A.getInstance()
        B._forgetClassInstanceReferenceForTesting()
        b = B.getInstance()
        assert b.__class__.__name__ == "B"
