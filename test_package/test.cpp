#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <variant>

#ifdef SHOULD_USE_LIBCXX
#   ifndef _LIBCPP_VERSION
#   error "Not using libc++"
#   endif
#endif

enum struct Foo : std::uint8_t
{
    First = 0,
    Second
};

enum struct Bar : std::uint8_t
{
    First = 0,
    Second
};

using S = std::variant< Foo, Bar >;

// template< std::size_t bla >
// struct print_size;

// print_size< sizeof( S ) > b;

#ifdef SHOULD_USE_LIBCXX
static_assert( sizeof( S ) == 3 );
#else
static_assert( sizeof( S ) == 2 );
#endif

int check( S const & bla )
{
    if ( std::holds_alternative< Bar >( bla ) )
    {
        throw std::invalid_argument( "wrong alternative!" );
    }
    return 0;
}

int main()
{
    std::cout << "Hello, world!" << std::endl;
#ifdef SHOULD_USE_LIBCXX
    std::cout << "I'm using libc++ 🎉" << std::endl;
#endif
    S bla = Foo::First;
    return check( bla );
}
