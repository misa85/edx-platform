.. _VitalSource:

#########################
VitalSource E-Reader Tool
#########################

The VitalSource Online Bookshelf e-reader tool provides your students with easy access to electronic books. Students can not only read text, but also quickly browse and search content (including figures and notes), create and manage multiple highlighters, and copy notes into external documents.

.. image:: /Images/VitalSource.png
   :width: 500
   :alt: VitalSource e-book with highlighted note

The VitalSource e-reader opens in a new browser page. You'll create a link to the e-reader in a unit in your course. 

.. image:: /Images/VitalSource_LMS.png
   :width: 500
   :alt: Student view of a unit that contains a VitalSource component

**************************
Add a VitalSource E-Reader
**************************

Adding a VitalSource e-reader has several steps:

#. Obtain the code for your e-book from VitalSource.
#. Modify your course's advanced settings.
#. Add the VitalSource e-reader to a unit.

=========================================
Step 1. Obtain the Code for Your E-Book
=========================================

To obtain the specific code for your e-book from VitalSource:

#. The course team selects a Member Publishing Point Person to work with your book's publisher and VitalSource.

#. The MPPP asks the publisher to send the e-book files to VitalSource. The publisher will work with VitalSource to make sure the e-book meets the VitalSource Online Bookshelf specifications.

#. VitalSource uploads the e-book to the Online Bookshelf and creates a specific code for the e-book.

#. VitalSource sends the e-book's code to the MPPP.

=========================================
Step 2. Modify the Advanced Settings
=========================================

In this step, you'll add values to the **advanced_modules** and **lti_passports** policy keys on the **Advanced Settings** page. 

.. note:: You must obtain the value for the **lti_passports** policy key from your VitalSource account manager.

#. In Studio, click the **Settings** menu, and then click **Advanced Settings**.

#. On the **Advanced Settings** page, locate the **advanced_modules** policy key.

#. Under **Policy Value**, place your cursor between the brackets, and then enter ``“lti”``. Make sure to include the quotation marks, but not the period.

   .. image:: /Images/LTIPolicyKey.png
    :alt: Image of the advanced_modules key in the Advanced Settings page, with the LTI value added

   **Note** If the **Policy Value** field already contains text, place your cursor directly after the closing quotation mark for the final item, and then enter a comma followed by ``“lti”`` (make sure that you include the quotation marks). For example, the text in the **Policy Value** field may resemble the following:

   ``"value_1","lti"``

4. Scroll down to the **lti_passports** policy key.

#. Under **Policy Value**, place your cursor between the brackets, and then enter the value for the **lti_passports** policy key that you obtained from your VitalSource account manager.

#. At the bottom of the page, click **Save Changes**.

The page refreshes automatically. At the top of the page, you see a notification that your changes have been saved.

==============================================
Step 3. Add the VitalSource E-Reader to a Unit
==============================================

To add the VitalSource e-reader to a unit, you'll create an LTI component, and then configure the component.

#. In the unit where you want to create the problem, click **Advanced** under **Add New Component**, and then click **LTI**.

#. In the component that appears, click **Edit**.

#. In the **Display Name** field, type the name of your e-book. This name appears at the top of the component and in the course ribbon at the top of the page in the courseware.

#. Next to **Custom Parameters**, click **Add**.

#. In the field that appears, enter the following (where ``VitalSource-code`` is the specific code for the e-book that the MPPP received from VitalSource):

   ``vbid=VitalSource-code``

   If you want to test an e-book, you can enter ``vbid=L-999-70103`` to create a link to *Pride and Prejudice*.

#. If you want your e-book to open to a specific page, click **Add** next to **Custom Parameters** again, and then add the following (where ``35`` is the page of the e-book):

   ``book_location=page/35``

#. In the **Launch URL** field, enter the following (make sure to use **https** instead of **http**):

  ``https://bc.vitalsource.com/books/book``

8. In the **LTI ID** field, enter the following:

  ``vital_source``

9. Click **Save**.
