# Generated by Django 3.1.6 on 2022-01-23 12:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nakhll_market', '0139_shop_in_campaign'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attribute',
            name='FK_User',
        ),
        migrations.RemoveField(
            model_name='attrprice',
            name='FK_Product',
        ),
        migrations.RemoveField(
            model_name='attrproduct',
            name='FK_Attribute',
        ),
        migrations.RemoveField(
            model_name='attrproduct',
            name='FK_Product',
        ),
        migrations.RemoveField(
            model_name='bankaccount',
            name='FK_Profile',
        ),
        migrations.RemoveField(
            model_name='category',
            name='FK_SubCategory',
        ),
        migrations.RemoveField(
            model_name='category',
            name='FK_User',
        ),
        migrations.RemoveField(
            model_name='market',
            name='FK_MarketManager',
        ),
        migrations.RemoveField(
            model_name='market',
            name='FK_Tag',
        ),
        migrations.RemoveField(
            model_name='market',
            name='FK_User',
        ),
        migrations.RemoveField(
            model_name='marketbanner',
            name='FK_Market',
        ),
        migrations.RemoveField(
            model_name='marketbanner',
            name='FK_Tag',
        ),
        migrations.RemoveField(
            model_name='marketbanner',
            name='FK_User',
        ),
        migrations.RemoveField(
            model_name='message',
            name='FK_Sender',
        ),
        migrations.RemoveField(
            model_name='message',
            name='FK_Users',
        ),
        migrations.RemoveField(
            model_name='optinalattribute',
            name='FK_Details',
        ),
        migrations.DeleteModel(
            name='Option_Meta',
        ),
        migrations.RemoveField(
            model_name='pages',
            name='FK_User',
        ),
        migrations.RemoveField(
            model_name='polling',
            name='FK_Product',
        ),
        migrations.RemoveField(
            model_name='polling',
            name='FK_Shop',
        ),
        migrations.RemoveField(
            model_name='polling',
            name='FK_Survey',
        ),
        migrations.RemoveField(
            model_name='polling',
            name='FK_User',
        ),
        migrations.RemoveField(
            model_name='productmovie',
            name='FK_Product',
        ),
        migrations.RemoveField(
            model_name='productmovie',
            name='FK_Tag',
        ),
        migrations.RemoveField(
            model_name='productmovie',
            name='FK_User',
        ),
        migrations.RemoveField(
            model_name='review',
            name='FK_Like',
        ),
        migrations.RemoveField(
            model_name='review',
            name='FK_NegativeNote',
        ),
        migrations.RemoveField(
            model_name='review',
            name='FK_PositiveNote',
        ),
        migrations.RemoveField(
            model_name='review',
            name='FK_Product',
        ),
        migrations.RemoveField(
            model_name='review',
            name='FK_User',
        ),
        migrations.RemoveField(
            model_name='review',
            name='FK_UserAdder',
        ),
        migrations.RemoveField(
            model_name='shopbanner',
            name='FK_Shop',
        ),
        migrations.RemoveField(
            model_name='shopbanner',
            name='FK_Tag',
        ),
        migrations.RemoveField(
            model_name='shopbanner',
            name='FK_User',
        ),
        migrations.RemoveField(
            model_name='shopcomment',
            name='FK_Like',
        ),
        migrations.RemoveField(
            model_name='shopcomment',
            name='FK_Pater',
        ),
        migrations.RemoveField(
            model_name='shopcomment',
            name='FK_Shop',
        ),
        migrations.RemoveField(
            model_name='shopcomment',
            name='FK_User',
        ),
        migrations.RemoveField(
            model_name='shopcomment',
            name='FK_UserAdder',
        ),
        migrations.RemoveField(
            model_name='shopmovie',
            name='FK_Shop',
        ),
        migrations.RemoveField(
            model_name='shopmovie',
            name='FK_Tag',
        ),
        migrations.RemoveField(
            model_name='shopmovie',
            name='FK_User',
        ),
        migrations.RemoveField(
            model_name='submarket',
            name='FK_Market',
        ),
        migrations.RemoveField(
            model_name='submarket',
            name='FK_Tag',
        ),
        migrations.RemoveField(
            model_name='submarket',
            name='FK_User',
        ),
        migrations.RemoveField(
            model_name='submarketbanner',
            name='FK_SubMarket',
        ),
        migrations.RemoveField(
            model_name='submarketbanner',
            name='FK_Tag',
        ),
        migrations.RemoveField(
            model_name='submarketbanner',
            name='FK_User',
        ),
        migrations.RemoveField(
            model_name='survey',
            name='FK_User',
        ),
        migrations.RemoveField(
            model_name='user_message_status',
            name='FK_User',
        ),
        migrations.RemoveField(
            model_name='userpoint',
            name='FK_User',
        ),
        migrations.RemoveField(
            model_name='alert',
            name='FK_Field',
        ),
        migrations.RemoveField(
            model_name='historicalproduct',
            name='FK_SubMarket',
        ),
        migrations.RemoveField(
            model_name='product',
            name='FK_Category',
        ),
        migrations.RemoveField(
            model_name='product',
            name='FK_ExceptionPostRange',
        ),
        migrations.RemoveField(
            model_name='product',
            name='FK_OptinalAttribute',
        ),
        migrations.RemoveField(
            model_name='product',
            name='FK_Points',
        ),
        migrations.RemoveField(
            model_name='product',
            name='FK_PostRange',
        ),
        migrations.RemoveField(
            model_name='product',
            name='FK_SubMarket',
        ),
        migrations.RemoveField(
            model_name='product',
            name='FK_Tag',
        ),
        migrations.RemoveField(
            model_name='productbanner',
            name='FK_Tag',
        ),
        migrations.RemoveField(
            model_name='shop',
            name='FK_SubMarket',
        ),
        migrations.RemoveField(
            model_name='shop',
            name='FK_Tag',
        ),
        migrations.DeleteModel(
            name='Attribute',
        ),
        migrations.DeleteModel(
            name='AttrPrice',
        ),
        migrations.DeleteModel(
            name='AttrProduct',
        ),
        migrations.DeleteModel(
            name='BankAccount',
        ),
        migrations.DeleteModel(
            name='Category',
        ),
        migrations.DeleteModel(
            name='Details',
        ),
        migrations.DeleteModel(
            name='Field',
        ),
        migrations.DeleteModel(
            name='Market',
        ),
        migrations.DeleteModel(
            name='MarketBanner',
        ),
        migrations.DeleteModel(
            name='Message',
        ),
        migrations.DeleteModel(
            name='Note',
        ),
        migrations.DeleteModel(
            name='OptinalAttribute',
        ),
        migrations.DeleteModel(
            name='Pages',
        ),
        migrations.DeleteModel(
            name='Polling',
        ),
        migrations.DeleteModel(
            name='PostRange',
        ),
        migrations.DeleteModel(
            name='ProductMovie',
        ),
        migrations.DeleteModel(
            name='Review',
        ),
        migrations.DeleteModel(
            name='ShopBanner',
        ),
        migrations.DeleteModel(
            name='ShopComment',
        ),
        migrations.DeleteModel(
            name='ShopMovie',
        ),
        migrations.DeleteModel(
            name='SubMarket',
        ),
        migrations.DeleteModel(
            name='SubMarketBanner',
        ),
        migrations.DeleteModel(
            name='Survey',
        ),
        migrations.DeleteModel(
            name='Tag',
        ),
        migrations.DeleteModel(
            name='User_Message_Status',
        ),
        migrations.DeleteModel(
            name='UserPoint',
        ),
    ]
