# from decimal import Decimal
#
# import pytest
#
# from src.ebf_domain.money.currency import USD, EUR, GBP, JPY
# from src.ebf_domain.money.money import Money, dollars_part, cents_part
#
#
# class TestMoneyCreation:
#     """Tests for Money creation and factory methods."""
#
#     class TestMint:
#
#         def test_mint_from_decimal(self):
#             """Can create Money from decimal using mint()."""
#             money = Money.mint(29.99, USD)
#
#             assert money.amount_cents == 2999
#             assert money.currency == USD
#             assert money.amount == Decimal('29.99')
#
#         def test_mint_from_int(self):
#             """Can mint Money from integer."""
#             money = Money.mint(100, USD)
#
#             assert money.amount_cents == 10000
#             assert money.amount == Decimal('100')
#
#         def test_mint_rounds_correctly(self):
#             """mint() rounds to nearest cent (not truncates)."""
#             # CRITICAL: This was a bug in the original
#             money = Money.mint(10.126, USD)
#
#             # Should round 10.126 -> 10.13 -> 1013 cents
#             assert money.amount_cents == 1013
#             assert money.amount == Decimal('10.13')
#
#         def test_mint_rounds_half_up(self):
#             """mint() uses ROUND_HALF_UP (0.5 rounds up)."""
#             money = Money.mint(10.125, USD)
#
#             assert money.amount_cents == 1013  # Rounds up
#
#         def test_mint_with_different_currency(self):
#             """Can mint with any currency."""
#             euros = Money.mint(50.00, EUR)
#
#             assert euros.currency == EUR
#             assert euros.amount_cents == 5000
#
#     class TestFromCents:
#
#         def test_from_cents_creates_money(self):
#             """from_cents() creates Money from integer cents."""
#             money = Money.from_cents(2999, USD)
#
#             assert money.amount_cents == 2999
#             assert money.amount == Decimal('29.99')
#
#         def test_from_cents_with_zero(self):
#             """from_cents() works with zero."""
#             money = Money.from_cents(0, USD)
#
#             assert money.is_zero
#
#         def test_from_cents_with_negative(self):
#             """from_cents() works with negative amounts."""
#             money = Money.from_cents(-500, USD)
#
#             assert money.amount == Decimal('-5.00')
#             assert money.is_negative
#
#     class TestZero:
#
#         def test_zero_creates_zero_money(self):
#             """zero() creates Money with amount 0."""
#             money = Money.zero(USD)
#
#             assert money.amount_cents == 0
#             assert money.is_zero
#
#         def test_zero_with_different_currency(self):
#             """zero() works with any currency."""
#             euros = Money.zero(EUR)
#
#             assert euros.is_zero
#             assert euros.currency == EUR
#
#     class TestLegacyCompatibility:
#
#         def test_from_db_alias(self):
#             """from_db() is alias for from_cents()."""
#             money = Money.from_db(2999, USD)
#
#             assert money.amount_cents == 2999
#
#
# class TestMoneyProperties:
#     """Tests for Money properties."""
#
#     class TestAmount:
#
#         def test_amount_property_returns_decimal(self):
#             """amount property returns Decimal."""
#             money = Money.from_cents(2999, USD)
#
#             amount = money.amount
#
#             assert isinstance(amount, Decimal)
#             assert amount == Decimal('29.99')
#
#     class TestDollarsPart:
#
#         def test_dollars_part_for_positive(self):
#             """dollars_part returns whole dollars."""
#             money = Money.mint(29.99, USD)
#
#             assert money.dollars_part == 29
#
#         def test_dollars_part_for_negative(self):
#             """dollars_part works with negative amounts."""
#             money = Money.mint(-29.99, USD)
#
#             assert money.dollars_part == -29
#
#         def test_dollars_part_for_whole_number(self):
#             """dollars_part for whole dollar amount."""
#             money = Money.mint(100.00, USD)
#
#             assert money.dollars_part == 100
#
#         def test_legacy_dollars_part_function(self):
#             """Legacy dollars_part() function works."""
#             money = Money.mint(29.99, USD)
#
#             assert dollars_part(money) == 29
#
#     class TestCentsPart:
#
#         def test_cents_part_for_positive(self):
#             """cents_part returns cents only."""
#             money = Money.mint(29.99, USD)
#
#             assert money.cents_part == 99
#
#         def test_cents_part_for_negative_is_positive(self):
#             """cents_part is always positive (absolute value)."""
#             money = Money.mint(-29.99, USD)
#
#             assert money.cents_part == 99  # Positive
#
#         def test_cents_part_for_whole_dollars(self):
#             """cents_part is 0 for whole dollar amounts."""
#             money = Money.mint(100.00, USD)
#
#             assert money.cents_part == 0
#
#         def test_legacy_cents_part_function(self):
#             """Legacy cents_part() function works."""
#             money = Money.mint(29.99, USD)
#
#             assert cents_part(money) == 99
#
#     class TestStatusChecks:
#
#         def test_is_zero(self):
#             """is_zero returns True for zero amount."""
#             assert Money.zero(USD).is_zero
#             assert not Money.mint(0.01, USD).is_zero
#
#         def test_is_positive(self):
#             """is_positive returns True for positive amount."""
#             assert Money.mint(10, USD).is_positive
#             assert not Money.zero(USD).is_positive
#             assert not Money.mint(-10, USD).is_positive
#
#         def test_is_negative(self):
#             """is_negative returns True for negative amount."""
#             assert Money.mint(-10, USD).is_negative
#             assert not Money.zero(USD).is_negative
#             assert not Money.mint(10, USD).is_negative
#
#
# class TestMoneyArithmetic:
#     """Tests for arithmetic operations."""
#
#     class TestAddition:
#
#         def test_add_same_currency(self):
#             """Can add Money with same currency."""
#             m1 = Money.mint(10.50, USD)
#             m2 = Money.mint(5.25, USD)
#
#             result = m1 + m2
#
#             assert result.amount == Decimal('15.75')
#             assert result.currency == USD
#
#         def test_add_optimized_for_cents(self):
#             """Addition works directly with cents (optimization)."""
#             m1 = Money.from_cents(1050, USD)
#             m2 = Money.from_cents(525, USD)
#
#             result = m1 + m2
#
#             assert result.amount_cents == 1575
#
#         def test_add_different_currencies_raises_error(self):
#             """Cannot add different currencies."""
#             usd = Money.mint(10, USD)
#             eur = Money.mint(10, EUR)
#
#             with pytest.raises(TypeError, match="different currencies"):
#                 usd + eur
#
#         def test_add_with_zero_for_sum_support(self):
#             """Can add 0 to support sum() function."""
#             money = Money.mint(10, USD)
#
#             result = money + 0
#
#             assert result == money
#
#         def test_sum_function_works(self):
#             """sum() works on list of Money."""
#             amounts = [
#                 Money.mint(10, USD),
#                 Money.mint(20, USD),
#                 Money.mint(30, USD)
#             ]
#
#             total = sum(amounts, Money.zero(USD))
#
#             assert total.amount == Decimal('60')
#
#     class TestSubtraction:
#
#         def test_subtract_same_currency(self):
#             """Can subtract Money with same currency."""
#             m1 = Money.mint(20.00, USD)
#             m2 = Money.mint(7.50, USD)
#
#             result = m1 - m2
#
#             assert result.amount == Decimal('12.50')
#
#         def test_subtract_different_currencies_raises_error(self):
#             """Cannot subtract different currencies."""
#             usd = Money.mint(10, USD)
#             eur = Money.mint(5, EUR)
#
#             with pytest.raises(TypeError, match="different currencies"):
#                 usd - eur
#
#         def test_subtract_larger_from_smaller(self):
#             """Can create negative Money from subtraction."""
#             m1 = Money.mint(5, USD)
#             m2 = Money.mint(10, USD)
#
#             result = m1 - m2
#
#             assert result.amount == Decimal('-5')
#             assert result.is_negative
#
#     class TestMultiplication:
#
#         def test_multiply_by_int(self):
#             """Can multiply Money by integer."""
#             money = Money.mint(10.50, USD)
#
#             result = money * 3
#
#             assert result.amount == Decimal('31.50')
#
#         def test_multiply_by_decimal(self):
#             """Can multiply Money by Decimal."""
#             money = Money.mint(100, USD)
#
#             result = money * Decimal("0.15")
#
#             assert result.amount == Decimal('15.00')
#
#         def test_multiply_by_float(self):
#             """Can multiply Money by float."""
#             money = Money.mint(20, USD)
#
#             result = money * 1.5
#
#             assert result.amount == Decimal('30.00')
#
#         def test_reverse_multiplication(self):
#             """Support scalar * Money."""
#             money = Money.mint(10, USD)
#
#             result = 3 * money
#
#             assert result.amount == Decimal('30')
#
#         def test_multiply_rounds_correctly(self):
#             """Multiplication rounds to nearest cent."""
#             money = Money.mint(10.00, USD)
#
#             result = money * Decimal("0.126")
#
#             # 10.00 * 0.126 = 1.26 -> 126 cents
#             assert result.amount_cents == 126
#
#         def test_multiply_by_money_raises_error(self):
#             """Cannot multiply Money by Money."""
#             m1 = Money.mint(10, USD)
#             m2 = Money.mint(5, USD)
#
#             with pytest.raises(TypeError, match="Cannot multiply Money by Money"):
#                 m1 * m2
#
#     class TestDivision:
#
#         def test_divide_by_int(self):
#             """Can divide Money by integer."""
#             money = Money.mint(30, USD)
#
#             result = money / 3
#
#             assert result.amount == Decimal('10.00')
#
#         def test_divide_by_decimal(self):
#             """Can divide Money by Decimal."""
#             money = Money.mint(100, USD)
#
#             result = money / Decimal("4")
#
#             assert result.amount == Decimal('25.00')
#
#         def test_divide_rounds_correctly(self):
#             """Division rounds to nearest cent."""
#             money = Money.mint(10.00, USD)
#
#             result = money / 3
#
#             # 10.00 / 3 = 3.333... -> rounds to 3.33
#             assert result.amount_cents == 333
#
#         def test_divide_by_money_raises_error(self):
#             """Cannot divide Money by Money."""
#             m1 = Money.mint(10, USD)
#             m2 = Money.mint(5, USD)
#
#             with pytest.raises(TypeError, match="Cannot divide Money by Money"):
#                 m1 / m2
#
#         def test_divide_by_zero_raises_error(self):
#             """Division by zero raises error."""
#             money = Money.mint(10, USD)
#
#             with pytest.raises(ZeroDivisionError):
#                 money / 0
#
#         def test_floor_division(self):
#             """Floor division works correctly."""
#             money = Money.mint(10, USD)
#
#             result = money // 3
#
#             assert result.amount_cents == 333  # 1000 // 3
#
#     class TestNegationAndAbs:
#
#         def test_negate_positive(self):
#             """Can negate positive Money."""
#             money = Money.mint(10, USD)
#
#             result = -money
#
#             assert result.amount == Decimal('-10')
#
#         def test_negate_negative(self):
#             """Can negate negative Money."""
#             money = Money.mint(-5, USD)
#
#             result = -money
#
#             assert result.amount == Decimal('5')
#
#         def test_abs_of_negative(self):
#             """Absolute value of negative Money."""
#             money = Money.mint(-15, USD)
#
#             result = abs(money)
#
#             assert result.amount == Decimal('15')
#
#         def test_abs_of_positive(self):
#             """Absolute value of positive is unchanged."""
#             money = Money.mint(15, USD)
#
#             result = abs(money)
#
#             assert result.amount == Decimal('15')
#
#
# class TestMoneyComparison:
#     """Tests for comparison operations."""
#
#     def test_equality_same_amount_and_currency(self):
#         """Equal Money objects are equal."""
#         m1 = Money.mint(10.50, USD)
#         m2 = Money.mint(10.50, USD)
#
#         assert m1 == m2
#
#     def test_equality_uses_cents_not_decimal(self):
#         """Equality compares cents directly."""
#         m1 = Money.from_cents(2999, USD)
#         m2 = Money.from_cents(2999, USD)
#
#         assert m1 == m2
#
#     def test_inequality_different_amount(self):
#         """Different amounts are not equal."""
#         m1 = Money.mint(10, USD)
#         m2 = Money.mint(20, USD)
#
#         assert m1 != m2
#
#     def test_inequality_different_currency(self):
#         """Different currencies are not equal."""
#         m1 = Money.mint(10, USD)
#         m2 = Money.mint(10, EUR)
#
#         assert m1 != m2
#
#     def test_less_than(self):
#         """< operator works."""
#         m1 = Money.mint(5, USD)
#         m2 = Money.mint(10, USD)
#
#         assert m1 < m2
#         assert not m2 < m1
#
#     def test_less_than_or_equal(self):
#         """<= operator works."""
#         m1 = Money.mint(10, USD)
#         m2 = Money.mint(10, USD)
#         m3 = Money.mint(15, USD)
#
#         assert m1 <= m2
#         assert m1 <= m3
#
#     def test_greater_than(self):
#         """> operator works."""
#         m1 = Money.mint(20, USD)
#         m2 = Money.mint(10, USD)
#
#         assert m1 > m2
#         assert not m2 > m1
#
#     def test_greater_than_or_equal(self):
#         """>= operator works."""
#         m1 = Money.mint(10, USD)
#         m2 = Money.mint(10, USD)
#         m3 = Money.mint(5, USD)
#
#         assert m1 >= m2
#         assert m1 >= m3
#
#     def test_comparison_different_currencies_raises_error(self):
#         """Comparing different currencies raises error."""
#         usd = Money.mint(10, USD)
#         eur = Money.mint(10, EUR)
#
#         with pytest.raises(TypeError, match="different currencies"):
#             usd < eur
#
#     def test_same_currency_method(self):
#         """same_currency() checks if currencies match."""
#         m1 = Money.mint(10, USD)
#         m2 = Money.mint(20, USD)
#         m3 = Money.mint(10, EUR)
#
#         assert m1.same_currency(m2)
#         assert not m1.same_currency(m3)
#
#     def test_currency_mismatch_method(self):
#         """currency_mismatch() checks if currencies differ."""
#         m1 = Money.mint(10, USD)
#         m2 = Money.mint(10, EUR)
#
#         assert m1.currency_mismatch(m2)
#         assert not m1.currency_mismatch(m1)
#
#
# class TestMoneySplitting:
#     """Tests for split() method."""
#
#     def test_split_evenly(self):
#         """Split money that divides evenly."""
#         money = Money.mint(30.00, USD)
#
#         parts = money.split(3)
#
#         assert len(parts) == 3
#         assert all(p.amount == Decimal("10.00") for p in parts)
#         assert sum(p.amount_cents for p in parts) == money.amount_cents
#
#     def test_split_with_remainder(self):
#         """Split with remainder distributes extra cents."""
#         money = Money.mint(10.00, USD)
#
#         parts = money.split(3)
#
#         assert len(parts) == 3
#         # First part gets the extra cent
#         assert parts[0].amount_cents == 334
#         assert parts[1].amount_cents == 333
#         assert parts[2].amount_cents == 333
#         # Sum equals original
#         assert sum(p.amount_cents for p in parts) == money.amount_cents
#
#     def test_split_preserves_currency(self):
#         """Split preserves currency."""
#         money = Money.mint(10, EUR)
#
#         parts = money.split(2)
#
#         assert all(p.currency == EUR for p in parts)
#
#     def test_split_into_one_part(self):
#         """Splitting into 1 part returns original amount."""
#         money = Money.mint(10.50, USD)
#
#         parts = money.split(1)
#
#         assert len(parts) == 1
#         assert parts[0] == money
#
#     def test_split_into_zero_parts_raises_error(self):
#         """Cannot split into zero parts."""
#         money = Money.mint(10, USD)
#
#         with pytest.raises(ValueError, match="must be positive"):
#             money.split(0)
#
#     def test_split_negative_money(self):
#         """Can split negative money."""
#         money = Money.mint(-10.00, USD)
#
#         parts = money.split(3)
#
#         # All parts should be negative
#         assert all(p.is_negative for p in parts)
#         assert sum(p.amount_cents for p in parts) == money.amount_cents
#
#
# class TestMoneyAllocation:
#     """Tests for allocate() method."""
#
#     def test_allocate_equal_ratios(self):
#         """Allocate with equal ratios."""
#         money = Money.mint(100.00, USD)
#
#         parts = money.allocate([1, 1, 1])
#
#         # Each gets ~33.33, with rounding adjustments
#         total = sum(p.amount_cents for p in parts)
#         assert total == money.amount_cents
#
#     def test_allocate_different_ratios(self):
#         """Allocate with different ratios."""
#         money = Money.mint(100.00, USD)
#
#         parts = money.allocate([1, 2, 2])  # 20%, 40%, 40%
#
#         assert parts[0].amount == Decimal("20.00")
#         assert parts[1].amount == Decimal("40.00")
#         assert parts[2].amount == Decimal("40.00")
#
#     def test_allocate_preserves_total(self):
#         """Allocation sum equals original."""
#         money = Money.mint(10.00, USD)
#
#         parts = money.allocate([3, 3, 3])
#
#         assert sum(p.amount_cents for p in parts) == money.amount_cents
#
#     def test_allocate_preserves_currency(self):
#         """Allocation preserves currency."""
#         money = Money.mint(100, EUR)
#
#         parts = money.allocate([1, 2])
#
#         assert all(p.currency == EUR for p in parts)
#
#     def test_allocate_empty_ratios_raises_error(self):
#         """Empty ratios list raises error."""
#         money = Money.mint(100, USD)
#
#         with pytest.raises(ValueError, match="non-empty"):
#             money.allocate([])
#
#     def test_allocate_zero_sum_raises_error(self):
#         """Ratios summing to zero raises error."""
#         money = Money.mint(100, USD)
#
#         with pytest.raises(ValueError, match="sum to non-zero"):
#             money.allocate([1, -1])
#
#
# class TestMoneyFormatting:
#     """Tests for string representations."""
#
#     def test_str_representation(self):
#         """str() returns formatted amount with symbol."""
#         money = Money.mint(29.99, USD)
#
#         assert str(money) == "$29.99"
#
#     def test_str_with_different_currency(self):
#         """str() uses currency symbol."""
#         euros = Money.mint(50.00, EUR)
#
#         assert str(euros) == "€50.00"
#
#     def test_str_with_jpy_no_decimals(self):
#         """str() respects currency precision (JPY has 0)."""
#         yen = Money.mint(1000, JPY)
#
#         assert str(yen) == "¥1000"
#
#     def test_repr_representation(self):
#         """repr() returns constructor form."""
#         money = Money.mint(29.99, USD)
#
#         assert repr(money) == "Money(2999, USD)"
#
#     def test_format_default(self):
#         """format() with defaults shows currency code."""
#         money = Money.mint(29.99, USD)
#
#         formatted = money.format()
#
#         assert formatted == "$29.99 USD"
#
#     def test_format_without_currency_code(self):
#         """format() can hide currency code."""
#         money = Money.mint(29.99, USD)
#
#         formatted = money.format(show_currency=False)
#
#         assert formatted == "$29.99"
#
#     def test_format_with_custom_symbol(self):
#         """format() can override symbol."""
#         money = Money.mint(29.99, USD)
#
#         formatted = money.format(symbol='US$')
#
#         assert formatted == "US$29.99 USD"
#
#
# class TestMoneyImmutability:
#     """Tests for immutability."""
#
#     def test_cannot_modify_amount_cents(self):
#         """Money is immutable (frozen)."""
#         money = Money.mint(10, USD)
#
#         with pytest.raises(Exception):  # FrozenInstanceError
#             money.amount_cents = 2000
#
#     def test_cannot_modify_currency(self):
#         """Cannot change currency after creation."""
#         money = Money.mint(10, USD)
#
#         with pytest.raises(Exception):
#             money.currency = EUR
#
#     def test_hashable_for_sets(self):
#         """Money objects are hashable."""
#         m1 = Money.mint(10, USD)
#         m2 = Money.mint(20, USD)
#         m3 = Money.mint(10, USD)
#
#         money_set = {m1, m2, m3}
#
#         assert len(money_set) == 2  # m1 and m3 are equal
#
#     def test_can_be_dict_key(self):
#         """Money can be used as dict key."""
#         price = Money.mint(29.99, USD)
#
#         prices = {price: "Premium"}
#
#         assert prices[price] == "Premium"
#
#
# class TestMoneyEdgeCases:
#     """Tests for edge cases."""
#
#     def test_very_large_amounts(self):
#         """Money handles very large amounts."""
#         money = Money.mint(999999999999.99, USD)
#
#         doubled = money * 2
#
#         assert doubled.amount == Decimal("1999999999999.98")
#
#     def test_very_small_fractions(self):
#         """Money handles small fractions (rounds to cents)."""
#         money = Money.mint(0.001, USD)
#
#         # 0.001 rounds to 0 cents
#         assert money.amount_cents == 0
#
#     def test_precision_maintained_through_operations(self):
#         """Integer cents maintain precision."""
#         m1 = Money.from_cents(10, USD)  # $0.10
#         m2 = Money.from_cents(20, USD)  # $0.20
#
#         result = m1 + m2
#
#         assert result.amount_cents == 30  # Exactly $0.30
#         assert result.amount == Decimal('0.30')
#
#     def test_different_currencies_independent(self):
#         """Different currencies work independently."""
#         usd = Money.mint(100, USD)
#         eur = Money.mint(100, EUR)
#         gbp = Money.mint(100, GBP)
#
#         assert usd != eur != gbp
#         assert (usd * 2).currency == USD
#         assert (eur * 2).currency == EUR
#         assert (gbp * 2).currency == GBP
