# setup.py
from setuptools import setup
from Cython.Build import cythonize

extra_compile_args = ["-O3", "-funroll-loops"]
extra_link_args = []

setup(
    name="bitmask_cy",
    ext_modules=cythonize(
        "bitmask_cy.pyx",
        compiler_directives={"language_level": "3", "boundscheck": False, "wraparound": False},
        # annotate=True,
    ),
    zip_safe=False,
)
